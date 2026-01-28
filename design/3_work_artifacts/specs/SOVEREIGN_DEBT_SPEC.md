# Phase 26.5 Specification: Sovereign Debt & Corporate Bailout System

**Status:** APPROVED (by Architect Prime)
**Version:** 1.1
**Primary Goal:** Transition from Magic Money/Grants to a Market-based Sovereign Debt and Senior Loan system.

## 1. Executive Decisions (Architect Prime)
- **Grace Period**: Firms aged < 24 Ticks are exempt from Altman Z-Score evaluation.
- **Runway Check**: Young firms must pass a "3-month wage runway" check to receive bailouts.
- **Crowding Out**: Market-driven bond yields will naturally compete with corporate loans. This is an intended economic realism.
- **CB Intervention (QE)**: Central Bank intervenes only if bond yields exceed 10.0%.

## 2. Technical Architecture

### 2.1 Corporate Solvency Check (The Filter)
To identify "Zombie Firms" while protecting startups.

**Logic:**
```python
def check_bailout_eligibility(firm, current_tick) -> bool:
    # 1. Grace Period for Startups
    if firm.age < 24:
        # Runway Check: (Cash + NearCash) / MonthlyWage >= 3.0
        return firm.cash_reserve >= (firm.total_wage_bill * 3.0)
    
    # 2. Altman Z-Score for Established Firms
    # Z = 1.2X1 + 1.4X2 + 3.3X3 (Simplified)
    # X1: Working Capital / Assets
    # X2: Equity (Net Worth) / Assets
    # X3: Avg Profit / Assets
    z_score = firm.calculate_altman_z_score()
    return z_score > 1.81  # Standard threshold
```

### 2.2 Bailout Refactoring (From Grant to Senior Debt)
- **Interest Rate**: `CentralBank.base_rate + 0.05` (5% Penalty Premium).
- **Covenants (Mandatory)**:
    - `dividends_allowed = False`
    - `executive_salary_freeze = True`
    - `mandatory_repayment = 0.5 * quarterly_profit` (when profitable)

### 2.3 Sovereign Debt Market (The Bond)
- **Issuance Priority**: Banks -> Households -> Central Bank (as Buyer of Last Resort).
- **Yield Calculation**: 
    - `Yield = Base_Rate + Risk_Premium(Debt_to_GDP)`
    - Risk Premium increases exponentially as Debt/GDP hits 0.6, 0.9, 1.2.

## 3. Implementation Blueprint (`modules/finance`)
- **API Definition**: `modules/finance/api.py` (Defines `BondDTO`, `BailoutLoanDTO`, `IFinanceSystem`).
- **Logic Module**: `modules/finance/system.py` (Manages evaluate_solvency, bond_auction, debt_servicing).
- **Agent Integration**:
    - `Government`: Calls `issue_treasury_bonds()` instead of printing money.
    - `Firm`: Updates `liabilities` and checks `covenants` before dividend/wage ticks.

## 4. Verification Plan
1. **Zombie Cleanup**: Verify a failing established firm (Z < 1.81) is liquidated.
2. **Infant Support**: Verify a promising startup (Z < 1.81, but with runway) receives a loan.
3. **Yield Spike**: Verify that massive government deficits push market interest rates up, affecting household consumption.

---
**Reporting**: Jules must log the average Z-Score of the economy and the impact of Yield Spikes on corporate investment to `communications/insights/`.
