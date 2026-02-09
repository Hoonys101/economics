```markdown
# Technical Specification: Judicial & Finance Refactor

**Version**: 1.0
**Date**: 2026-02-09
**Author**: Gemini Scribe

## 1. Part 1: Judicial Seizure Waterfall

### 1.1. Overview & Goal
This specification details the design of a hierarchical asset seizure mechanism, "The Waterfall," for the `JudicialSystem`. This resolves the "All-or-Nothing" limitation identified in `TD-JUD-ASSET` by introducing a prioritized, multi-stage liquidation process. When a loan default occurs, the system will attempt to recover the debt by seizing assets in the following order: Cash, Liquid Stocks, and finally, Inventory. If the debt remains outstanding after all asset classes are liquidated, a formal debt restructuring process is initiated via an event, ensuring architectural decoupling.

### 1.2. Interfaces (`modules/governance/judicial/api.py`)

```python
# modules/governance/judicial/api.py
from typing import TypedDict, List, Literal, Optional
from modules.events.dtos import LoanDefaultedEvent
from modules.system.api import IEventBus

# --- Data Transfer Objects ---

class SeizureRequestDTO(TypedDict):
    """Input for initiating a seizure, derived from a default event."""
    agent_id: int
    creditor_id: int
    outstanding_debt: float
    loan_id: str
    tick: int

class AssetSeizureResult(TypedDict):
    """Details the outcome of seizing a single asset class."""
    asset_class: Literal["cash", "stocks", "inventory"]
    amount_recovered: float
    success: bool
    details: str

class SeizureWaterfallResultDTO(TypedDict):
    """The final summary of the entire seizure waterfall process."""
    agent_id: int
    total_amount_recovered: float
    remaining_debt: float
    stages: List[AssetSeizureResult]
    restructuring_required: bool

class DebtRestructuringRequiredEvent(TypedDict):
    """
    Event published when seizure fails to cover the full debt.
    This signals the need for Chapter 11-style reorganization.
    """
    event_type: Literal["DEBT_RESTRUCTURING_REQUIRED"]
    tick: int
    defaulter_id: int
    creditor_id: int
    uncovered_debt: float
    original_loan_id: str

# --- Interfaces ---

class IJudicialSystem:
    """
    Orchestrates legal and punitive consequences within the economy.
    """
    def __init__(self, event_bus: IEventBus, ...):
        ...

    def handle_financial_event(self, event: LoanDefaultedEvent) -> None:
        """Subscribes to and processes financial default events."""
        ...

    def execute_seizure_waterfall(self, request: SeizureRequestDTO) -> SeizureWaterfallResultDTO:
        """
        Orchestrates the multi-stage asset seizure process.
        This is a pure orchestration method, not a calculation one.
        """
        ...
```

### 1.3. Logic & Architecture (Pseudo-code)
The `JudicialSystem` acts as a pure orchestrator, delegating valuation and transfer tasks to specialized systems.

```python
# In JudicialSystem.execute_seizure_waterfall:

def execute_seizure_waterfall(self, request: SeizureRequestDTO) -> SeizureWaterfallResultDTO:
    # 1. Initialization
    remaining_debt = request['outstanding_debt']
    total_recovered = 0.0
    results: List[AssetSeizureResult] = []
    agent = self.agent_registry.get_agent(request['agent_id'])
    creditor = self.agent_registry.get_agent(request['creditor_id'])

    if not agent or not creditor:
        # Return early if agents don't exist
        ...

    # 2. STAGE 1: Seize Cash
    if remaining_debt > 0 and isinstance(agent, IFinancialEntity):
        cash_balance = agent.assets # Per IFinancialEntity contract
        amount_to_seize = min(cash_balance, remaining_debt)
        if amount_to_seize > 0:
            tx_success = self.settlement_system.transfer(agent, creditor, amount_to_seize, ...)
            if tx_success:
                remaining_debt -= amount_to_seize
                total_recovered += amount_to_seize
                results.append({'asset_class': 'cash', 'amount_recovered': amount_to_seize, ...})

    # 3. STAGE 2: Liquidate Stocks
    # This assumes a portfolio handler that can liquidate assets.
    if remaining_debt > 0 and isinstance(agent, IPortfolioHandler):
        # The JudicialSystem does NOT value the portfolio. It requests liquidation.
        # A hypothetical PortfolioManager would handle the sale and return proceeds.
        liquidation_proceeds = self.portfolio_manager.liquidate_for_value(agent.id, remaining_debt)
        if liquidation_proceeds > 0:
            # Transfer proceeds from the agent's now-liquidated holdings to the creditor
            tx_success = self.settlement_system.transfer(agent, creditor, liquidation_proceeds, ...)
            if tx_success:
                 remaining_debt -= liquidation_proceeds
                 total_recovered += liquidation_proceeds
                 results.append({'asset_class': 'stocks', 'amount_recovered': liquidation_proceeds, ...})

    # 4. STAGE 3: Liquidate Inventory
    # Leverages the ILiquidatable protocol from TD-269.
    if remaining_debt > 0 and isinstance(agent, ILiquidatable):
        # Delegate to a dedicated liquidation handler.
        liquidation_proceeds = self.inventory_liquidation_handler.liquidate_for_value(agent.id, remaining_debt)
        if liquidation_proceeds > 0:
            tx_success = self.settlement_system.transfer(agent, creditor, liquidation_proceeds, ...)
            if tx_success:
                remaining_debt -= liquidation_proceeds
                total_recovered += liquidation_proceeds
                results.append({'asset_class': 'inventory', 'amount_recovered': liquidation_proceeds, ...})

    # 5. FINAL STAGE: Trigger Reorganization if Necessary
    restructuring_required = remaining_debt > 0
    if restructuring_required:
        restructuring_event = DebtRestructuringRequiredEvent(
            event_type="DEBT_RESTRUCTURING_REQUIRED",
            tick=request['tick'],
            defaulter_id=request['agent_id'],
            creditor_id=request['creditor_id'],
            uncovered_debt=remaining_debt,
            original_loan_id=request['loan_id']
        )
        self.event_bus.publish("DEBT_RESTRUCTURING_REQUIRED", restructuring_event)

    # 6. Return comprehensive result DTO
    return SeizureWaterfallResultDTO(
        agent_id=request['agent_id'],
        total_amount_recovered=total_recovered,
        remaining_debt=remaining_debt,
        stages=results,
        restructuring_required=restructuring_required
    )
```

### 1.4. Risk & Impact Audit
This design directly addresses the risks identified in the pre-flight audit:
- **[RISK-1 Mitigated] SRP Violation**: The `JudicialSystem` is a pure orchestrator. It does not contain valuation logic. It queries other systems (`IFinancialEntity` for balance, delegates to `PortfolioManager` and `InventoryLiquidationHandler`) and commands `SettlementSystem` for transfers.
- **[RISK-2 Mitigated] Circular Dependency**: The Chapter 11/Reorganization flow is decoupled via the `DebtRestructuringRequiredEvent`. `JudicialSystem`'s responsibility ends upon publishing this event. A separate `FinanceSaga` or `RestructuringEngine` will subscribe to it, preventing a direct call from Governance to Finance.
- **[RISK-3 Mitigated] Incomplete Protocols**: The logic explicitly uses `isinstance()` checks for `IFinancialEntity`, `IPortfolioHandler`, and `ILiquidatable` at each stage of the waterfall, ensuring it can gracefully handle agents that do not implement all protocols.

### 1.5. Verification Plan
- **Test Case 1 (Full Cash)**: Defaulting agent has enough cash to cover the debt. Verify only cash is seized and `remaining_debt` is 0.
- **Test Case 2 (Cash + Stocks)**: Agent's cash is insufficient, but cash + stock value covers the debt. Verify both are liquidated and `remaining_debt` is 0.
- **Test Case 3 (All Assets)**: Debt is covered only after seizing cash, stocks, and inventory. Verify all three stages are executed.
- **Test Case 4 (Insolvency)**: Total asset value is less than the debt. Verify all assets are seized and a `DebtRestructuringRequiredEvent` is published to the event bus with the correct `uncovered_debt`.
- **Test Case 5 (Missing Protocol)**: Agent implements `IFinancialEntity` and `ILiquidatable` but not `IPortfolioHandler`. Verify the waterfall correctly skips Stage 2 (Stocks) and proceeds to Stage 3 (Inventory).

---

## 2. Part 2: Finance Command Pattern

### 2.1. Overview & Goal
This specification details the refactoring of `FinanceSystem.grant_bailout_loan` to resolve the technical debt item `TD-FIN-PURE`. The existing implementation violates the stateless service principle by mixing validation logic with stateful side-effects. The new design transforms the function into a pure, stateless command generator. It will perform validations and return a `FinanceCommand` DTO. An external Saga Orchestrator (e.g., within `GovernmentOrchestrator`) will be responsible for executing the command and applying all side-effects, adhering to the project's established Saga/Orchestrator pattern.

### 2.2. Interfaces (`modules/finance/api.py`)

```python
# modules/finance/api.py
from typing import TypedDict, Optional, Literal
from modules.finance.domain import BailoutCovenant

# --- Data Transfer Objects ---

class BailoutRequestDTO(TypedDict):
    """Input from an orchestrator to request a bailout loan."""
    firm_id: int
    amount: float
    current_tick: int

class GrantBailoutCommand(TypedDict):
    """
    Output DTO encapsulating the validated *intent* of a bailout.
    This command is processed by a Saga Orchestrator to execute side-effects.
    """
    command_type: Literal["GRANT_BAILOUT_LOAN"]
    firm_id: int
    government_id: int # ID of the lender
    amount: float
    interest_rate: float
    covenants: BailoutCovenant
    tick: int

class InsufficientGovernmentFundsError(Exception):
    """Raised when the government cannot afford the bailout."""
    pass

# --- Interfaces ---

class IFinanceSystem:
    """Manages sovereign debt, corporate bailouts, and solvency checks."""

    # ... (other methods)

    def request_bailout_loan(self, request: BailoutRequestDTO) -> GrantBailoutCommand:
        """
        [NEW] Stateless function to validate and create a bailout loan command.
        Raises InsufficientGovernmentFundsError on failure.
        """
        ...

    def grant_bailout_loan(self, ...) -> ...:
        """
        [DEPRECATED] This method will be removed in favor of the
        stateless request_bailout_loan and an external orchestrator.
        """
        raise DeprecationWarning("Use request_bailout_loan() and a Saga Orchestrator.")

```

### 2.3. Logic & Architecture (Saga Pattern)
The interaction is split into two distinct phases: **Command Generation** (stateless) and **Command Execution** (stateful).

**Phase 1: Command Generation (Inside `FinanceSystem`)**
```python
# In FinanceSystem.request_bailout_loan

def request_bailout_loan(self, request: BailoutRequestDTO) -> GrantBailoutCommand:
    # 1. Validation: Check Government Budget
    gov_balance = self.government.assets.get(DEFAULT_CURRENCY, 0.0)
    if gov_balance < request['amount']:
        raise InsufficientGovernmentFundsError(f"Gov funds {gov_balance} < required {request['amount']}")

    # 2. Calculation: Determine loan terms
    base_rate = self.central_bank.get_base_rate()
    penalty_premium = self.config_module.get("economy_params.BAILOUT_PENALTY_PREMIUM", 0.05)
    covenants = BailoutCovenant(
        dividends_allowed=False,
        executive_salary_freeze=True,
        mandatory_repayment=self.config_module.get("economy_params.BAILOUT_COVENANT_RATIO", 0.5)
    )

    # 3. Create & Return Command DTO (NO SIDE EFFECTS)
    return GrantBailoutCommand(
        command_type="GRANT_BAILOUT_LOAN",
        firm_id=request['firm_id'],
        government_id=self.government.id,
        amount=request['amount'],
        interest_rate=base_rate + penalty_premium,
        covenants=covenants,
        tick=request['current_tick']
    )
```

**Phase 2: Command Execution (Inside `GovernmentOrchestrator`)**
```python
# In GovernmentOrchestrator.process_turn or similar

def _execute_bailout_saga(self, firm_id: int, amount: float):
    # 1. Request the command from the pure service
    try:
        request_dto = BailoutRequestDTO(firm_id=firm_id, amount=amount, current_tick=self.tick)
        bailout_command = self.finance_system.request_bailout_loan(request_dto)
    except InsufficientGovernmentFundsError as e:
        logger.warning(f"BAILOUT_DENIED | {e}")
        return

    # 2. Execute Side-Effects based on the command
    firm = self.agent_registry.get_agent(bailout_command['firm_id'])
    government = self.agent_registry.get_agent(bailout_command['government_id'])

    # 2a. Settle funds
    tx_success = self.settlement_system.transfer(
        debit_agent=government,
        credit_agent=firm,
        amount=bailout_command['amount'],
        memo=f"Bailout Loan {firm_id}"
    )

    if not tx_success:
        logger.error("Bailout Saga failed at settlement stage.")
        # Optional: Implement compensation logic (rollback)
        return

    # 2b. Update firm's state
    # This should be done via a clear protocol method, not direct attribute setting
    if isinstance(firm, IBorrower): # Hypothetical protocol
        firm.add_debt(bailout_command['amount'])
        firm.set_covenants(bailout_command['covenants'])

    # 2c. Persist transaction for auditing (TBD)
    # ... logic to save the transaction record ...

    logger.info(f"Bailout Saga completed for Firm {firm_id}.")
```

### 2.4. Risk & Impact Audit
- **[DEBT RESOLVED] TD-FIN-PURE**: This design directly resolves the technical debt by transforming `grant_bailout_loan` into the stateless `request_bailout_loan`, fully aligning with the project's Saga/Orchestrator architecture.
- **[Impact] Significant Refactoring Required**: This is a breaking change. All existing callers of `grant_bailout_loan` must be refactored to use the new two-phase saga pattern. The `GovernmentOrchestrator` will now own the stateful execution logic.
- **[Impact] Test Invalidation**: All unit and integration tests for the old `grant_bailout_loan` are now invalid. They must be rewritten. New tests will focus on:
    1.  Validating the `GrantBailoutCommand` DTO returned by `request_bailout_loan`.
    2.  Verifying the correct sequence of side-effects in the `GovernmentOrchestrator` when it processes the command.

### 2.5. Verification Plan
- **Test `request_bailout_loan` (Stateless Service)**:
    - **Test Case 1**: Given a valid request, verify that the returned `GrantBailoutCommand` DTO contains the correct data (amount, calculated rate, etc.).
    - **Test Case 2**: Mock the government's assets to be less than the requested amount. Verify that `InsufficientGovernmentFundsError` is raised.
- **Test `GovernmentOrchestrator` (Saga Executor)**:
    - **Test Case 3**: Provide a valid `GrantBailoutCommand`. Verify that `settlement_system.transfer` is called with the correct parameters and that the firm's state is updated correctly via its public protocol.

---
## 3. Mandatory Reporting Verification
Insights and potential technical debt discovered during the implementation of these specifications (e.g., need for a `PortfolioManager` or `IBorrower` protocol) will be documented in a new file under `communications/insights/` upon completion of the implementation task, as required by the Scribe protocol.
```
