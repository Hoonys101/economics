📄 Drafting Spec with instruction: 'WO-068: CPR System Enhancement Spec. Resolve TD-008 and TD-009. Goals: 1) Replace primitive valuation logic with Solvency/Liquidity metrics to avoid bailing out zombie firms. 2) Convert unconditional grants to Government Loans requiring repayment with interest. 3) Track fiscal impact of bailouts in Government.total_debt. Include: Data structures (BailoutRequestDTO, LoanContractDTO), pseudo-code for eligibility check, and test cases.'...
📖 Attached context: simulation/systems/bootstrapper.py
📖 Attached context: simulation/agents/government.py
📖 Attached context: config.py
🚀 [GeminiWorker] Running task with manual: spec_writer.md

✅ Spec Draft Saved: C:\coding\economics\design\drafts\draft_WO_068__CPR_System_Enhancement.md
============================================================

✅ Spec Draft Saved: C:\coding\economics\design\drafts\draft_WO_068__CPR_System_Enhancement.md
============================================================
Running `gemini_worker.py spec "WO-068: CPR System Enhancement..."`...

Here are the draft specifications and API contracts for **WO-068: Economic CPR System Enhancement**.

### 1. Module Contract (`simulation/systems/cpr/api.py`)

```python
"""
simulation/systems/cpr/api.py

Economic CPR (Critical Preservative Resuscitation) System Interface.
Replaces the legacy 'Bootstrapper' with a solvency-based Lender of Last Resort mechanism.
"""

from typing import List, Dict, Any, Optional, Protocol, TypedDict
from dataclasses import dataclass
from enum import Enum

# --- DTOs ---

class BailoutStatus(Enum):
    APPROVED = "APPROVED"
    REJECTED_ZOMBIE = "REJECTED_ZOMBIE"     # Solvency too low, no recovery chance
    REJECTED_SUFFICIENT = "REJECTED_SUFFICIENT" # Liquidity is fine
    REJECTED_BUDGET = "REJECTED_BUDGET"     # Government cannot afford

@dataclass
class FinancialHealthDTO:
    """Snapshot of a firm's financial health for triage."""
    firm_id: str
    total_assets: float
    total_liabilities: float
    current_cash: float
    avg_profit_margin: float  # Last 10 ticks
    solvency_ratio: float     # Assets / Liabilities
    liquidity_ratio: float    # Cash / Monthly Burn

@dataclass
class BailoutLoanContractDTO:
    """The finalized loan agreement."""
    contract_id: str
    lender_id: int            # Government ID
    borrower_id: str          # Firm ID
    principal_amount: float
    interest_rate: float      # Annualized
    start_tick: int
    duration_ticks: int
    remaining_balance: float
    status: str = "ACTIVE"    # ACTIVE, DEFAULTED, REPAID

class BailoutResultDTO(TypedDict):
    request_id: str
    firm_id: str
    status: BailoutStatus
    loan_contract: Optional[BailoutLoanContractDTO]
    reason: str

# --- Interfaces ---

class IFirmAgent(Protocol):
    """Protocol for Firm agents interacting with CPR."""
    id: str
    assets: float
    cash: float
    liabilities: float
    
    def get_profit_history(self) -> List[float]: ...
    def add_liability(self, contract: BailoutLoanContractDTO) -> None: ...
    def receive_cash(self, amount: float) -> None: ...

class IGovernmentAgent(Protocol):
    """Protocol for Government interacting with CPR."""
    id: int
    assets: float
    total_debt: float
    
    # Registry of active loans held by the government
    bailout_portfolio: List[BailoutLoanContractDTO]

    def can_afford(self, amount: float) -> bool: ...
    def disburse_loan(self, contract: BailoutLoanContractDTO) -> bool: ...

class IEconomicCPR(Protocol):
    """
    Main Interface for the CPR System.
    """
    def scan_and_rescue(
        self, 
        firms: List[IFirmAgent], 
        government: IGovernmentAgent, 
        current_tick: int
    ) -> List[BailoutResultDTO]:
        """
        Executes the Triage -> Assess -> Rescue pipeline.
        Returns a list of actions taken.
        """
        ...

    def process_repayments(
        self, 
        firms: List[IFirmAgent], 
        government: IGovernmentAgent, 
        current_tick: int
    ) -> float:
        """
        Calculates and executes loan repayments from Firms to Government.
        Returns total amount recovered.
        """
        ...
```

### 2. Detailed Specification (`design/specs/economic_cpr_spec.md`)

```markdown
# Spec: WO-068 Economic CPR System Enhancement

## 1. Overview
- **Goal**: Replace the primitive `Bootstrapper.inject_initial_liquidity` (Helicopter Money) with a rigorous "Lender of Last Resort" mechanism.
- **Problem (TD-008/TD-009)**: The current system keeps "Zombie Firms" alive by injecting free resources indefinitely, distorting market competition and inflation.
- **Solution**: Implement a Triage system that only lends to "Illiquid but Solvent" firms. Bailouts become loans with interest, not grants.

## 2. Technical Architecture

### 2.1. Triage Logic (The Filter)
The CPR system classifies firms into three zones based on `FinancialHealthDTO`:

1.  **Green Zone (Healthy)**:
    - `Liquidity Ratio` > `CPR_LIQUIDITY_MIN` (e.g., 0.5 months of burn)
    - **Action**: Do nothing.

2.  **Yellow Zone (Distressed)**:
    - `Liquidity Ratio` < `CPR_LIQUIDITY_MIN`
    - `Solvency Ratio` > `CPR_SOLVENCY_MIN` (e.g., 1.0, Assets > Liabilities)
    - `Profit Margin` > `CPR_MIN_PROFITABILITY` (e.g., -0.1, not losing >10% per tick)
    - **Action**: **Eligible for Bailout Loan.**

3.  **Red Zone (Zombie)**:
    - `Solvency Ratio` < `CPR_SOLVENCY_MIN` (Insolvent)
    - OR `Profit Margin` < `CPR_MIN_PROFITABILITY` (Deeply unprofitable)
    - **Action**: **Deny Bailout.** Allow Liquidation/M&A mechanics to take over (Creative Destruction).

### 2.2. Loan Mechanism (The Contract)
Instead of `firm.assets += amount`, we execute a loan transaction:

1.  **Terms Calculation**:
    - `Principal`: Amount needed to restore Liquidity to `CPR_LIQUIDITY_TARGET`.
    - `Interest Rate`: `Government.base_rate` + `CPR_RISK_PREMIUM` (Penalty rate to discourage reliance).
    - `Duration`: `CPR_LOAN_DURATION` (e.g., 50 ticks).

2.  **Execution Flow**:
    - Check Government Budget (or Debt Ceiling if deficit spending enabled).
    - Transfer Cash: Gov -> Firm.
    - Create `BailoutLoanContractDTO`.
    - Firm adds Contract to `liabilities`.
    - Gov adds Contract to `bailout_portfolio` (Assets).

3.  **Repayment (Daily Processing)**:
    - Every tick, firms pay `(Principal + Interest) / Duration`.
    - If Firm cannot pay -> Default Logic (Asset Seizure / Bankruptcy acceleration).

## 3. Configuration Constants (to be added to `config.py`)

| Constant | Value | Description |
| :--- | :--- | :--- |
| `CPR_LIQUIDITY_MIN` | 0.2 | Cash threshold (20% of monthly burn) to trigger scan |
| `CPR_SOLVENCY_MIN` | 0.8 | Minimum Assets/Liabilities ratio to be viable |
| `CPR_LIQUIDITY_TARGET` | 1.0 | Target liquidity after bailout |
| `CPR_RISK_PREMIUM` | 0.05 | Additional interest rate above base rate (5%) |
| `CPR_LOAN_DURATION` | 60 | Loan repayment term in ticks |
| `CPR_ZOMBIE_TOLERANCE` | 3 | Max bailouts allowed per firm per year |

## 4. Pseudo-code Logic

### 4.1. Scan and Rescue
```python
def scan_and_rescue(firms, government, tick):
    results = []
    
    for firm in firms:
        # 1. Analyze Health
        health = analyze_health(firm)
        
        # 2. Triage
        if health.liquidity_ratio >= CONFIG.CPR_LIQUIDITY_MIN:
            continue # Healthy
            
        if health.solvency_ratio < CONFIG.CPR_SOLVENCY_MIN:
            results.append(Reject(firm, "ZOMBIE_INSOLVENT"))
            continue
            
        # 3. Calculate Needs
        burn_rate = calculate_burn_rate(firm)
        needed = (CONFIG.CPR_LIQUIDITY_TARGET * burn_rate) - firm.cash
        
        # 4. Check Government Constraints
        if not government.can_afford(needed):
            results.append(Reject(firm, "GOV_BROKE"))
            continue
            
        # 5. Issue Loan
        contract = create_loan_contract(firm, government, needed)
        government.disburse_loan(contract)
        firm.add_liability(contract)
        
        results.append(Approve(firm, contract))
        
    return results
```

### 4.2. Repayment Cycle
```python
def process_repayments(firms, government, tick):
    recovered = 0.0
    for contract in government.bailout_portfolio:
        firm = get_firm(contract.borrower_id)
        
        payment = calculate_daily_payment(contract)
        
        if firm.cash >= payment:
            firm.cash -= payment
            government.assets += payment
            contract.remaining_balance -= (payment - interest_component)
            recovered += payment
        else:
            handle_default(firm, contract)
            
    return recovered
```

## 5. Verification Plan
- **Test Case 1: The Solvent Struggle**: Create a firm with high Assets (Machine) but 0 Cash. Verify CPR grants a loan.
- **Test Case 2: The Walking Dead**: Create a firm with Liabilities > Assets and negative profit. Verify CPR rejects bailout (Zombie).
- **Test Case 3: Repayment**: Verify Government assets increase over time as valid firms repay loans.

## 6. Mandatory Reporting (Jules)
Jules must report the following to `communications/insights/`:
1.  **Zombie Detection Rate**: How many firms are rejected due to insolvency vs. how many are saved?
2.  **Default Rate**: What percentage of CPR loans actually get repaid?
3.  **Fiscal Impact**: Does the CPR system cause a Government Debt spiral?
```

### 3. Action Items for Jules
1.  Create `modules/cpr/` directory (or `simulation/systems/cpr/`).
2.  Implement `api.py` as defined above.
3.  Implement `cpr_system.py` logic following the Spec.
4.  Update `Government` agent to implement `IGovernmentAgent` (add `bailout_portfolio`).
5.  Update `Firm` agent to implement `IFirmAgent` (add `liabilities` tracking).
6.  Run `verify_banking.py` (or create `verify_cpr.py`) to confirm logic.

============================================================
