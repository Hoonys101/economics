# W-1 Specification: Economic Reflux System (Phase 8-B)

> **Status**: Approved
> **Author**: Architect Prime (Refined by Antigravity)
> **Objective**: Implement "Economic Reflux" to enforce the identity $Income \equiv Expenditure$ and eliminate money "black holes".

## 1. Goal & Concept
Currently, certain expenses by Firms (Marketing, Fixed Costs, CAPEX) are simply subtracted from their cash balance and disappear from the economy. This causes deflationary pressure and eventual collapse (liquidity crisis).
The **Economic Reflux System** captures these "sunk costs" into a pool and redistributes them to households, simulating an "Implicit Service Sector" where households work and earn income.

## 2. Architecture

### 2.1 New System: `EconomicRefluxSystem`
*   **Path**: `simulation/systems/reflux_system.py`
*   **Role**:
    *   Acts as a sink for all "non-wage" expenses from Firms.
    *   Acts as a sink for "retained earnings" logic in Banks (forcing 100% payout).
    *   Distributes collected funds to Households at the end of every tick.

### 2.2 Class Definition
```python
# simulation/systems/reflux_system.py

class EconomicRefluxSystem:
    def __init__(self):
        self.balance: float = 0.0
        self.transaction_log: list = [] # Optional: for debugging

    def capture(self, amount: float, source: str, category: str):
        """
        Captures money that would otherwise vanish.
        :param amount: Amount to capture
        :param source: 'Firm_ID' or 'Bank'
        :param category: 'marketing', 'capex', 'fixed_cost', 'net_profit'
        """
        if amount > 0:
            self.balance += amount
            # logging if needed

    def distribute(self, households: list):
        """
        Distributes the total balance equally to all households.
        Simulates dividends and service sector wages.
        """
        if not households or self.balance <= 0:
            return

        total_amount = self.balance
        amount_per_household = total_amount / len(households)
        
        for agent in households:
            agent.assets += amount_per_household
            # Record this as 'service_sector_income' or 'other_income'
            # If agent has a method to record specific income, use it.
            # Otherwise, just add to assets and maybe log.
            if hasattr(agent, 'income_history'):
                 agent.income_history['service'] = agent.income_history.get('service', 0) + amount_per_household

        self.balance = 0.0 # Reset
```

## 3. Integration Points

### 3.1 `simulation/engine.py`
*   Initialize `self.reflux_system = EconomicRefluxSystem()` in `__init__`.
*   **Dependency Injection**:
    *   When calling `firm.update()`, pass `self.reflux_system`.
    *   When calling `bank.update()` (or `process_profits`), pass `self.reflux_system`.
*   **End of Tick**:
    *   Call `self.reflux_system.distribute(self.households)` AFTER all agents have moved but BEFORE statistics are calculated.

### 3.2 `simulation/firms.py` (`Firm`)
*   **Signature Update**: Update `update()` or relevant methods to accept `reflux_system`.
*   **Logic Change**:
    *   **Marketing**: Instead of just `self.cash -= marketing_cost`, do:
        ```python
        self.cash -= marketing_cost
        reflux_system.capture(marketing_cost, self.id, 'marketing')
        ```
    *   **Fixed Costs / Maintenance**:
        ```python
        self.cash -= fixed_cost
        reflux_system.capture(fixed_cost, self.id, 'fixed_cost')
        ```
    *   **Expansion (CAPEX)**:
        ```python
        self.cash -= expansion_cost
        reflux_system.capture(expansion_cost, self.id, 'capex')
        ```

### 3.3 `simulation/agents/bank.py` (`Bank`)
*   **Logic Change**:
    *   Ensure `net_profit` implies all interest income minus interest expense.
    *   Instead of retaining earnings, 100% of `net_profit` should be captured.
    *   `reflux_system.capture(net_profit, "Bank", 'dividends')`
    *   Bank cash balance should effectively remain neutral relative to profits (checking account balances are separate).

## 4. Verification
*   **Metric**: `Total Money Supply` should remain constant (or only grow via Central Bank injection).
*   **Check**: Run a simulation. If `reflux_pool.balance` is 0 at the start of next the tick, and Household assets have increased by that amount, it is working.
