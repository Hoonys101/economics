# Technical Specification: Holy Ledger Remediation (TD-127, TD-128, TD-129, TD-130)

## 1. Overview

**Objective**: This document outlines the technical plan to remediate critical architectural flaws by establishing the `SettlementSystem` as the exclusive authority for all cash-based asset movements within the simulation. This will enforce zero-sum integrity, ensure full auditability, and eliminate the class of "money leak" bugs.

**Scope**: This refactor targets the following modules, which currently perform direct or un-audited asset manipulation:
- `simulation/systems/event_system.py`
- `simulation/systems/lifecycle_manager.py`
- `simulation/systems/immigration_manager.py`
- `simulation/systems/ma_manager.py`

## 2. Core Mandates & Principles

1.  **Single Source of Truth**: The `SettlementSystem` is the **only** component authorized to modify an agent's cash balance. All cash creation, destruction, and transfers **must** be executed via its API.
2.  **No Direct Asset Mutation**: Direct calls to `agent.assets +=`, `agent.assets -=`, `agent.deposit()`, or `agent.withdraw()` from outside the agent's own decision-making logic are strictly forbidden. These will be replaced by calls to the `SettlementSystem`.
3.  **Mandatory Dependency Injection**: The `SettlementSystem` instance will be a **required, non-optional constructor argument** for all high-level system managers. Checks for its existence (e.g., `if hasattr(state, 'settlement_system')`) must be removed.
4.  **Deprecation of `RefluxSystem`**: The `RefluxSystem` is declared obsolete. Its responsibilities are absorbed by the `SettlementSystem`. It creates money and operates as a conflicting ledger, violating the core principle of a single source of truth.
5.  **Definition of "Asset Movement"**: For the scope of this remediation, an "asset movement" is strictly defined as a change in an agent's **fungible cash balance**. The transfer of non-fungible assets (e.g., inventory, capital stock) or changes to policy variables (e.g., tax rates) are not recorded as cash transactions, though their *consequences* (e.g., tax payments, liquidation proceeds) are.

## 3. API Modifications: `simulation.systems.settlement_system.py`

The `SettlementSystem` API will be expanded to handle all required transaction types.

```python
# simulation/systems/api.py (or a new dedicated settlement_api.py)

class ITransaction(TypedDict):
    # ... existing fields
    pass

class ISettlementSystem(Protocol):

    def transfer(self, source: Agent, destination: Agent, amount: float, reason: str, tick: int) -> ITransaction:
        """Transfers cash between two agents."""
        ...

    def create_and_transfer(self, source_authority: Union[Government, CentralBank], destination: Agent, amount: float, reason: str, tick: int) -> ITransaction:
        """Creates new money and transfers it to an agent (e.g., stimulus, grants)."""
        ...

    def transfer_and_destroy(self, source: Agent, sink_authority: Union[Government, CentralBank], amount: float, reason: str, tick: int) -> ITransaction:
        """Transfers money from an agent to an authority to be destroyed (e.g., taxes, loan repayment)."""
        ...

    def record_liquidation(self, agent: Agent, inventory_value: float, capital_value: float, recovered_cash: float, reason: str, tick: int) -> None:
        """
        Records the outcome of an asset liquidation.
        The system calculates the net asset destruction (inventory_value + capital_value - recovered_cash)
        and logs it to the money supply ledger.
        """
        ...
```

## 4. Module-Specific Refactoring Plan

### 4.1. `simulation.systems.lifecycle_manager.py`

- **Dependency Injection**:
  ```python
  # __init__(self, config_module: Any, demographic_manager: ..., inheritance_manager: ..., firm_system: ..., settlement_system: ISettlementSystem, logger: ...)
  self.settlement_system = settlement_system
  ```

- **Code Modifications**:
    - **Firm Liquidation**: The entire block handling manual asset distribution will be replaced.
      - **Before**: Direct manipulation of `firm.assets`, employee state, and shareholder assets. Use of `reflux_system`.
      - **After**:
        1. Calculate `total_cash` from `firm.assets`.
        2. Calculate `inv_value` and `capital_value`.
        3. Call `self.settlement_system.record_liquidation(...)` to log asset destruction.
        4. If `total_cash > 0`, iterate through shareholders and use `self.settlement_system.transfer(firm, shareholder, distribution_amount, "liquidation_dividend", tick)` to distribute proceeds.
        5. Any remaining un-owned cash is transferred to the government: `self.settlement_system.transfer(firm, self.government, remaining_cash, "liquidation_escheatment", tick)`.
        6. The `firm`'s assets are now considered zero by the ledger.

    - **Household Liquidation**:
      - **Before**: Use of `reflux_system`.
      - **After**:
        1. `InheritanceManager` will now also require `SettlementSystem` and return a list of `ITransaction` objects to be processed, ensuring all inheritance transfers are logged.
        2. Replace `reflux_system.capture(inv_value, ...)` with a call to `self.settlement_system.record_liquidation(household, inv_value, 0, 0, "household_liquidation", tick)`. The recovered cash is zero because it is handled via inheritance.

### 4.2. `simulation.systems.immigration_manager.py`

- **Dependency Injection**:
  ```python
  # __init__(self, config_module: Any, settlement_system: ISettlementSystem)
  self.settlement_system = settlement_system
  ```

- **Code Modifications**:
    - **Immigrant Funding**:
      - **Before**: `engine.government.withdraw(initial_assets)`
      - **After**: `self.settlement_system.create_and_transfer(engine.government, household, initial_assets, "immigration_grant", engine.time)`

### 4.3. `simulation.systems.ma_manager.py` (Mergers & Acquisitions)

- **Dependency Injection**:
  ```python
  # __init__(self, simulation: "Simulation", config_module: Any, settlement_system: ISettlementSystem)
  self.settlement_system = settlement_system
  ```

- **Code Modifications**:
    - **Merger Payment**:
      - **Before**: `predator.withdraw(price)` and `target_agent.deposit(price)`.
      - **After**: `self.settlement_system.transfer(predator, target_agent, price, f"M&A Acquisition {prey.id}", tick)`
    - **State Capture**:
      - **Before**: `predator.withdraw(price)` and `self.simulation.government.deposit(price)`.
      - **After**: `self.settlement_system.transfer(predator, self.simulation.government, price, f"M&A Acquisition {prey.id} (State)", tick)`
    - **Bankruptcy**:
      - The existing partial implementation is a good start. It must be finalized.
      - **Before**: `firm.liquidate_assets()` followed by a call to `settlement_system.record_liquidation_loss`.
      - **After**: `liquidated_value = firm.assets + firm.capital_stock + ...`. `recovered_cash = firm.liquidate_assets()`. Then call `self.settlement_system.record_liquidation(firm, liquidated_value - recovered_cash, 0, recovered_cash, "bankruptcy", tick)`. The core logic inside `liquidate_assets` must also be refactored to use `settlement_system` for any fund transfers.

### 4.4. `simulation.systems.event_system.py`

- **Dependency Injection**:
  ```python
  # __init__(self, config: Any, settlement_system: ISettlementSystem)
  self.settlement_system = settlement_system
  ```

- **Code Modifications**:
    - **Hyperinflation (Cash Injection)**:
      - **Before**: `h.assets *= (1 + injection_rate)`
      - **After**:
        ```python
        central_bank = context["central_bank"]
        for h in households:
            amount = h.assets * config.demand_shock_cash_injection
            self.settlement_system.create_and_transfer(
                central_bank, h, amount, "hyperinflation_stimulus", time
            )
        ```
    - **Deflation (Asset Shock)**:
      - **Before**: `agent.assets *= (1 - reduction_rate)`
      - **After**:
        ```python
        central_bank = context["central_bank"] # The "sink" authority
        for agent in households + firms:
            amount_to_destroy = agent.assets * config.asset_shock_reduction
            self.settlement_system.transfer_and_destroy(
                agent, central_bank, amount_to_destroy, "deflationary_shock", time
            )
        ```
    - **Policy Overrides**: The direct setting of `corporate_tax_rate` and `base_rate` will remain as "dirty hacks" for stress testing, as they are policy changes, not direct asset movements. The *effects* of these changes (tax payments) will be captured by the ledger through other systems.

## 5. Test & Verification Strategy

1.  **Unit Tests for `SettlementSystem`**: A dedicated test file, `tests/systems/test_settlement_system.py`, will be created to validate its internal logic, ensuring all operations are zero-sum and that the total money supply is tracked accurately.
2.  **Mocking `SettlementSystem`**: All tests for the affected manager modules will be refactored to inject a `MagicMock` of `ISettlementSystem`.
3.  **Assertion Refactoring**: Test assertions must be changed from checking agent state to verifying `settlement_system` calls.

    - **Example Test Refactor**:
      ```python
      # Before
      def test_immigration_creates_funded_household(engine):
          # ... setup ...
          initial_gov_assets = engine.government.assets
          immigration_manager.process_immigration(engine)
          new_immigrant = engine.households[-1]
          assert new_immigrant.assets > 0
          assert engine.government.assets < initial_gov_assets

      # After
      def test_immigration_creates_funded_household(engine, mock_settlement_system):
          # ... setup ...
          immigration_manager = ImmigrationManager(config, mock_settlement_system)
          immigration_manager.process_immigration(engine)
          
          # Assert that a transfer was requested
          mock_settlement_system.create_and_transfer.assert_called_once()
          call_args = mock_settlement_system.create_and_transfer.call_args
          assert call_args.kwargs['source_authority'] == engine.government
          assert call_args.kwargs['destination'].id == engine.households[-1].id
          assert call_args.kwargs['amount'] > 0
      ```

## 6. Addressing Pre-flight Audit Risks

-   **Dueling Ledgers**: Resolved by deprecating `RefluxSystem` and consolidating its logic into `SettlementSystem`.
-   **God Object Dependencies**: Resolved by mandating `SettlementSystem` as a direct, non-optional constructor dependency for all managers.
-   **Ambiguous "Asset Movement"**: Resolved by strictly scoping this work to fungible cash transactions.
-   **Un-audited Money Movements**: Resolved by replacing all direct asset modifications (`.withdraw`, `h.assets *=`) with explicit `SettlementSystem` API calls (`.transfer`, `.create_and_transfer`, etc.).
-   **Test Impact**: Addressed by the Test & Verification Strategy, which requires migrating tests to a mock-based approach, ensuring robustness against implementation changes.
