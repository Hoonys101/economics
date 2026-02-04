# WO-4.3 Political Component Implementation Insights

## Technical Debt
1. **Government Stance Proxy**: Currently, `PoliticalComponent` assumes a binary stance for political parties (BLUE=0.9, RED=0.1). A more sophisticated model would have the Government agent expose a continuous `fiscal_stance` or `policy_score` that reflects its actual policy decisions (tax rates, spending), allowing for more nuanced ideological matching.
2. **Missing `PoliticalComponent` Interface**: While `ISocialComponent` exists, `PoliticalComponent` does not implement an interface defined in `api.py`. It is currently a concrete class dependency in `Household`. Future refactoring should introduce `IPoliticalComponent` for better decoupling and testing.
3. **`market_data` Coupling**: We injected government data into `market_data` in `prepare_market_data`. While effective, `market_data` is becoming a "god object" for context. A dedicated `SocioPoliticalContextDTO` might be cleaner in the future.

## Insights
1. **Stateless Decomposition Pattern**: The pattern of "Stateless Component + State DTO" proved effective again here. It allowed `PoliticalComponent` to be purely functional, making unit testing trivial (as seen in `test_political_component.py`).
2. **Integration Complexity**: The main challenge was ensuring `Household` had access to global Government state (ruling party). Injecting this via `market_data` was the least invasive solution given the current architecture where `Household.update_needs` only receives `market_data`.
3. **Trust Dynamics**: The trust damper mechanism (`trust < 0.2 => approval = 0`) creates a hysteresis effect where once trust is lost, it is hard to regain approval even if policies align. This adds realistic inertia to political dynamics.
