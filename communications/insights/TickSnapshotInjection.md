# Tick-Snapshot Injection & Market Context Refactor

## Context
Mission: Implement 'Tick-Snapshot Injection' to capture exchange rates at tick start and inject them into a new `MarketContextDTO` for O(1) AI access.

## Technical Debt & Architecture Insights

### 1. Legacy Market Data Injection (The O(N) Problem)
Currently, `prepare_market_data` (in `utils.py`) constructs a `Dict[str, Any]` containing various market signals.
- **Issue**: This dictionary is loosely typed and requires string key lookups.
- **AI Access**: AI agents (via `StateBuilder`) iterate over this dictionary or perform multiple lookups to find relevant data (e.g., `goods_market` prices).
- **Exchange Rates**: There was no centralized injection of exchange rates. If an agent needed to value assets in multiple currencies, it would theoretically need to call `CurrencyExchangeEngine` individually, which is inefficient (O(N) calls to engine) and breaks the "snapshot" principle if rates were to change mid-tick (though they currently don't).

### 2. MarketContextDTO Solution
We introduced `MarketContextDTO` to provide a structured, strongly-typed container for global market context that is valid for the *entire tick*.
- **Content**: Initially contains `exchange_rates: Dict[CurrencyCode, float]`.
- **Injection**: The `EconomicIndicatorTracker` (which holds the `ExchangeEngine`) captures this snapshot at the beginning of the decision phase via `capture_market_context()`.
- **O(1) Access**: Agents receive this DTO in `DecisionContext`. AI can access `context.market_context.exchange_rates[currency]` directly without overhead.

### 3. Future Roadmap
- **Deprecate `market_data` Dict**: The goal is to move all fields from the legacy `market_data` dictionary into `MarketSnapshotDTO` (for market-specifics) and `MarketContextDTO` (for global context).
- **StateBuilder Update**: `StateBuilder.build_state` should be updated to prioritize reading from these DTOs instead of the raw dictionary.

### 4. Implementation Details
- **Tracker as Source**: `EconomicIndicatorTracker` was chosen as the source because it already initializes and manages the `CurrencyExchangeEngine`.
- **Purity**: By capturing rates once and passing the DTO, we ensure all agents see the exact same rates for a given tick, enforcing simulation determinism.
