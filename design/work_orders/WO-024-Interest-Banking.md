# Work Order: WO-024 Interest & Banking System (Operation "Money Multiplier")

## 1. Objective
Implement a **Fractional Reserve Banking System** to introduce **Interest Income** (Phase 14-3) and **Credit Creation**.
This transforms the economy from a strict "Cash Only" system to a "Credit" system, allowing capital to flow from savers (Households) to borrowers (Firms) via an intermediary (Bank).

## 2. Core Concepts

### 2.1 The Money Multiplier
- **Reserve Ratio ($R$)**: The portion of deposits the bank must keep in the vault (e.g., 10%).
- **Lending ($L$)**: The rest ($1-R$) is lent out to firms.
- **Effect**: Initial Deposit $D$ creates Total Money Supply $M = D \times (1/R)$.

### 2.2 Interest Rates
- **Deposit Rate ($r_d$)**: Paid to households. Reward for deferred consumption.
- **Loan Rate ($r_l$)**: Charged to firms. Cost of leverage.
- **Spread ($S$)**: $r_l - r_d$. The Bank's profit margin.

## 3. Implementation Plan

### 3.1 Configuration (`config.py`)
```python
# WO-024: Banking Config
BANK_RESERVE_RATIO = 0.10  # 10% Reserve
BANK_DEPOSIT_RATE_INITIAL = 0.03 # 3% APY
BANK_LOAN_RATE_INITIAL = 0.05    # 5% APY
```

### 3.2 Bank Agent (`simulation/agents/bank.py`)
*Create a new `CommercialBank` class (or update `CentralBank` if singular)*
- **Attributes**:
    - `total_deposits`: Sum of all household deposits.
    - `total_reserves`: Cash held in vault.
    - `total_loans`: Outstanding loans to firms.
    - `deposit_rate`: Dynamic.
    - `loan_rate`: Dynamic.
- **Methods**:
    - `deposit(agent_id, amount)`: Accept cash, update balance.
    - `withdraw(agent_id, amount)`: Return cash if reserves allow.
    - `request_loan(firm_id, amount)`: Grant loan if reserves allow (Credit Creation).
    - `pay_interest(current_tick)`: Accrue interest to depositors.

### 3.3 Household Updates (`simulation/core_agents.py`)
- **New Decisions**:
    - `deposit_decision`: How much excess cash to put in the bank?
        - Driven by `preference_asset` (Conservative/Miser types like banks).
        - Driven by `deposit_rate` (Yield chasing).
- **Asset Split**: Separate `cash` (wallet) vs `savings` (bank).

### 3.4 Firm Updates (`simulation/firms.py`)
- **Leverage Logic**:
    - Firms borrowing to expand production (CapEx) or cover liquidity crises.
    - **Bankruptcy**: Defaults on loans destroy Bank Capital (Risk).

## 4. Verification Plan (Test Plan C)
**Script**: `scripts/verify_banking.py`
1. **Spread Verify**: $Loan Rate > Deposit Rate$.
2. **Multiplier Effect**: Total Liabilities can exceed Base Money (High Leverage).
3. **Passive Income**: Households receiving Interest Income (check logs/DB).

## 5. Success Criteria
- **Liquidity**: Cash doesn't sit idle under mattresses; it flows to efficient firms.
- **Stability**: Bank runs (everyone withdrawing at once) are possible if Reserve Ratio is too low (Simulated Risk).
