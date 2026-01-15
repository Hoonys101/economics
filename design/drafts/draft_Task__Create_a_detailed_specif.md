I will create the design specifications and API definitions for the **Sovereign Debt & Corporate Bailout System** (Phase 26).

This design introduces a `FinanceSystem` module that acts as the intermediary between the Government, Central Bank, and Firms/Households, managing debt instruments instead of direct cash transfers.

### Work Output

1.  **`design/specs/sovereign_debt_spec.md`**: Detailed logic for Altman Z-Score filtering, Senior Debt issuance with covenants, and the Bond Market mechanism.
2.  **`modules/finance/api.py`**: API scaffolding defining the DTOs (`BondDTO`, `BailoutLoanDTO`) and the `IFinanceSystem` interface.

---

### 1. `modules/finance/api.py`

```python
"""
modules/finance/api.py
Description: Defines the interface and data structures for the Sovereign Debt and Corporate Bailout System.
This module manages financial instruments (Bonds, Loans) and solvency evaluations.
"""

from typing import Dict, List, Optional, Union, Any, TypedDict
from dataclasses import dataclass
from abc import ABC, abstractmethod

# --- DTO Definitions ---

@dataclass
class BondDTO:
    """
    Data Transfer Object representing a Government Bond (Sovereign Debt).
    """
    bond_id: str
    issuer_id: int  # Typically Government ID
    face_value: float
    coupon_rate: float  # Annual interest rate (e.g., 0.03 for 3%)
    maturity_tick: int
    issue_tick: int
    holder_id: Optional[int] = None  # Agent ID of the current owner (Bank, Household, CB)
    holder_type: str = "unassigned"  # 'bank', 'household', 'central_bank'

@dataclass
class BailoutLoanDTO:
    """
    Data Transfer Object representing a Senior Bailout Loan to a distressed Firm.
    """
    loan_id: str
    debtor_firm_id: int
    principal: float
    interest_rate: float
    issue_tick: int
    maturity_tick: int
    remaining_balance: float
    status: str  # 'active', 'defaulted', 'repaid'
    # Covenants
    covenant_freeze_dividends: bool = True
    covenant_freeze_salaries: bool = True

class SolvencyScoreDTO(TypedDict):
    """
    Result of an Altman Z-Score analysis.
    """
    firm_id: int
    z_score: float
    is_solvent: bool
    components: Dict[str, float]  # Breakdown: 'liquidity', 'retained_earnings', 'ebit'
    recommendation: str  # 'bailout', 'liquidate', 'monitor'

# --- Interface Definitions ---

class IFinanceSystem(ABC):
    """
    Interface for the centralized Finance System handling Debt and Bonds.
    """

    @abstractmethod
    def evaluate_solvency(self, firm_agent: Any, market_data: Dict[str, Any]) -> SolvencyScoreDTO:
        """
        Calculates the modified Altman Z-Score for a firm to determine bailout eligibility.
        """
        ...

    @abstractmethod
    def request_bailout(self, firm_agent: Any, amount_needed: float, current_tick: int) -> Optional[BailoutLoanDTO]:
        """
        Processes a bailout request.
        1. Checks solvency.
        2. If eligible, issues Senior Debt (BailoutLoanDTO).
        3. Applies covenants to the Firm agent.
        """
        ...

    @abstractmethod
    def issue_treasury_bonds(self, government_agent: Any, deficit_amount: float, current_tick: int) -> List[BondDTO]:
        """
        Issues government bonds to cover fiscal deficits.
        Executes a market auction to determine yield and sell bonds to Banks/Households/CB.
        """
        ...

    @abstractmethod
    def process_debt_servicing(self, current_tick: int) -> Dict[str, float]:
        """
        Daily routine:
        1. Collects interest payments from Bailout Loans.
        2. Pays coupons on Government Bonds.
        Returns a summary of flows.
        """
        ...
```

### 2. `design/specs/sovereign_debt_spec.md`

```markdown
# Phase 26 Specification: Sovereign Debt & Corporate Bailout System

## 1. Overview
This specification transitions the simulation's fiscal mechanisms from "Magic Money/Grants" to a **Debt-Based System**. It introduces two core subsystems:
1.  **Corporate Bailout Mechanism**: Replacing free subsidies with Senior Debt Loans containing strict covenants, guarded by an Altman Z-Score solvency check.
2.  **Sovereign Debt Market**: Replacing automatic deficit printing with Treasury Bond issuance, purchased by market participants (Banks, Households, Central Bank).

## 2. Data Structures (See `modules/finance/api.py`)

### 2.1 Core DTOs
-   **`BailoutLoanDTO`**: Represents a liability for the Firm and an asset for the Government.
    -   Key Attributes: `principal`, `interest_rate`, `covenant_freeze_dividends`.
-   **`BondDTO`**: Represents a liability for the Government and an asset for the Holder.
    -   Key Attributes: `coupon_rate`, `maturity_tick`, `holder_type`.
-   **`SolvencyScoreDTO`**: Outcome of the Z-Score analysis.

## 3. Detailed Logic & Algorithms

### 3.1 Corporate Solvency Check (Modified Altman Z-Score)
To prevent "Zombie Firms" from draining resources, bailouts are conditional.

**Formula**: $Z = 1.2X_1 + 1.4X_2 + 3.3X_3$
*   $X_1$ (Liquidity): `(Current Assets - Current Liabilities) / Total Assets`
*   $X_2$ (Accumulated Profit): `Retained Earnings / Total Assets`
*   $X_3$ (Performance): `Operating Profit (EBIT) / Total Assets`

**Pseudo-code**:
```python
def evaluate_solvency(firm, market_data) -> SolvencyScoreDTO:
    total_assets = firm.assets + firm.inventory_value + firm.fixed_capital
    if total_assets <= 0:
        return {"z_score": -99, "is_solvent": False, "recommendation": "liquidate"}

    # X1: Working Capital
    working_capital = firm.assets - firm.short_term_debt
    x1 = working_capital / total_assets

    # X2: Retained Earnings (Proxy: Net Worth / Assets)
    x2 = (firm.assets - firm.total_debt) / total_assets

    # X3: EBIT (Proxy: Recent average profit)
    avg_profit = mean(firm.profit_history[-10:])
    x3 = avg_profit / total_assets

    z_score = (1.2 * x1) + (1.4 * x2) + (3.3 * x3)

    # Thresholds (Configurable in config.py)
    Z_THRESHOLD = 1.81  # Standard distress zone threshold
    
    is_solvent = z_score > Z_THRESHOLD
    
    return {
        "z_score": z_score,
        "is_solvent": is_solvent,
        "recommendation": "bailout" if is_solvent else "liquidate"
    }
```

### 3.2 Bailout Execution (The "Rescue" Protocol)
If a firm is solvent but illiquid, it receives a loan, not a grant.

**Process**:
1.  **Request**: Firm triggers `request_bailout` when `assets < CRITICAL_LEVEL`.
2.  **Evaluation**: Call `evaluate_solvency`.
    *   **Fail**: Return `None`. Firm proceeds to bankruptcy/exit logic.
    *   **Pass**: Proceed to step 3.
3.  **Loan Issuance**:
    *   Create `BailoutLoanDTO`.
    *   Interest Rate: `Base Rate + Risk Premium (Penalty Rate ~5-10%)`.
    *   **Transfer**: `Government.assets -= Amount`, `Firm.assets += Amount`.
4.  **Covenant Application**:
    *   Set `Firm.covenants.dividends_allowed = False`.
    *   Set `Firm.covenants.wage_cap = True` (Executive/Worker wage freeze).

### 3.3 Sovereign Debt Issuance (Bond Market)
When Government runs a deficit (`expenditure > revenue`), it must issue bonds.

**Pseudo-code**:
```python
def issue_treasury_bonds(government, deficit, current_tick):
    bond_face_value = 1000.0
    num_bonds = ceil(deficit / bond_face_value)
    
    # 1. Determine Yield (Market Auction Simulation)
    base_rate = CentralBank.get_base_rate()
    # Supply/Demand logic: More debt -> Higher yield
    debt_to_gdp = government.total_debt / government.gdp_ema
    risk_premium = max(0.0, (debt_to_gdp - 0.5) * 0.05) 
    auction_yield = base_rate + risk_premium

    # 2. Buyer Allocation Priority
    # Tier 1: Commercial Banks (Regulatory requirement + Safety)
    # Tier 2: Households (Savings)
    # Tier 3: Central Bank (QE - Buyer of Last Resort)
    
    unsold_bonds = num_bonds
    issued_bonds = []

    # --- Tier 1: Banks ---
    for bank in banks:
        buy_amt = bank.decide_bond_purchase(auction_yield)
        # Process transaction...
    
    # --- Tier 2: Households ---
    # ... logic for households ...

    # --- Tier 3: QE (If enabled) ---
    if unsold_bonds > 0 and CentralBank.is_qe_enabled():
        CentralBank.buy_bonds(unsold_bonds)
        unsold_bonds = 0
    
    # 3. Bookkeeping
    government.assets += (num_bonds - unsold_bonds) * bond_face_value
    government.total_debt += num_bonds * bond_face_value
    
    return issued_bonds
```

## 4. Configuration & Constants
Add to `config.py`:
-   `BAILOUT_MIN_Z_SCORE`: 1.6 (Stricter than reality for simulation stability)
-   `BAILOUT_PENALTY_RATE`: 0.05 (5% above base rate)
-   `BOND_FACE_VALUE`: 1000.0
-   `QE_TRIGGER_YIELD`: 0.10 (If bond yields hit 10%, CB intervenes)

## 5. Implementation Steps
1.  Create `modules/finance/` directory.
2.  Implement `SolvencyEvaluator` class.
3.  Implement `BondMarket` class.
4.  Update `Government` to use `BondMarket` instead of negative assets.
5.  Update `Firm` to track `loans` and `covenants`.

## 6. Verification Plan
-   **Test Case 1: The Zombie Filter**: Create a firm with high assets but massive losses. Verify `evaluate_solvency` recommends "liquidate".
-   **Test Case 2: Covenant Enforcement**: Bailout a firm. Ensure it stops paying dividends in the next tick.
-   **Test Case 3: Debt Spiral**: Force Gov deficit. Verify bond yields rise as `debt_to_gdp` increases.

---
**Insights Reporting**:
*   Jules: Please report in `communications/insights/` if the Z-Score threshold (1.81) causes mass extinctions of firms during the initial "learning phase" of the simulation. We may need a "Grace Period" for young firms.
*   Jules: Monitor if the Bond Market drains too much liquidity from Banks, causing a credit crunch for Firms (Crowding Out Effect).
```
