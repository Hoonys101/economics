# CurrencyExchangeEngine Implementation Insights

## Technical Debt & Considerations
1.  **Static Parity**: The current implementation reads static parity from `config/simulation.yaml`. Real-world exchange rates fluctuate. Future phases might require a dynamic exchange rate model based on supply and demand or economic indicators.
2.  **ConfigManager Dependency**: The engine relies on `ConfigManager` (or similar object) having a `.get()` method supporting dot notation for nested keys. This couples the engine to the specific configuration loading mechanism.
3.  **Base Currency Hardcoding**: `DEFAULT_CURRENCY` is assumed to be USD (1.0). If the base currency changes, the logic holding USD as 1.0 might need review, although it's currently fetched from config or defaulted.
4.  **Error Handling**: If config is missing, it defaults to USD=1.0. This might mask configuration errors.

## Implementation Details
-   `CurrencyExchangeEngine` uses lazy loading for parity configuration to avoid reading config during initialization if not needed immediately.
-   It provides `get_exchange_rate` and `convert` methods.
-   `modules/finance/exchange/engine.py` is the location.
