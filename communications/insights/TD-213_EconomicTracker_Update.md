# EconomicTracker & Multi-Currency Valuation Insights (TD-213)

## Technical Debts Identified

### 1. Firm Financial Snapshot Currency Flaw
The method `FinanceDepartment.get_financial_snapshot` (delegated from `Firm`) calculates `total_assets` by summing `usd_balance` (DEFAULT_CURRENCY only), Inventory Value (in USD), and Capital Stock (in USD).
It fails to include assets held in other currencies.
- **Location**: `simulation/components/finance_department.py`
- **Impact**: Firms holding significant foreign currency reserves will appear undervalued in financial reports and aggregated metrics.
- **Workaround**: `EconomicIndicatorTracker` currently manually reconstructs the correct total value by calculating the full wallet value (converted to USD) and adding the non-cash components derived from the snapshot.

### 2. M2 Money Supply Definition Ambiguity
The `get_m2_money_supply` method aggregates "Money Supply" by summing:
- Household Wallet Balances
- Firm Wallet Balances
- Bank Reserves (Assets)
- Government Assets

**Issues**:
- **Government Assets**: Traditionally, M2 includes currency in circulation + deposits. Government deposits at the Central Bank are typically *excluded* from M2. If the Government holds assets in commercial banks, they might be included. The current implementation sums `government.assets`, which requires clarification on where these assets are held (Central Bank vs Commercial Bank).
- **Asset Types**: The calculation treats all "assets" in wallets as M2 components. In a multi-currency system, this implies M2 is an aggregate of all currencies converted to USD, rather than just USD money supply. This effectively tracks "Global Liquidity" rather than a specific currency's M2.

## Recommendations
1.  **Refactor FinanceDepartment**: Update `get_financial_snapshot` to iterate over all wallet balances and convert them using `CurrencyExchangeEngine`.
2.  **Clarify Monetary Aggregates**: Define whether `money_supply` tracks Global M2 (all currencies) or local M2 (USD only). If Global, the current approach is acceptable. If Local, we must filter for `DEFAULT_CURRENCY` only.
