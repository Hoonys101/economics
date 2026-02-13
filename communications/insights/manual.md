# PublicManager DTO Signature Mismatch Fix

## [Architectural Insights]
The `MarketSignalDTO` is a frozen dataclass used for cross-boundary data transfer, specifically for market signals.
It was updated to include `total_bid_quantity` and `total_ask_quantity` fields, which are crucial for market depth analysis and understanding liquidity.
However, the test `tests/unit/modules/system/execution/test_public_manager_compliance.py` was instantiating `MarketSignalDTO` without these required fields, leading to a `TypeError`.
This highlights the importance of keeping test data fixtures in sync with DTO schema changes.
By adding `total_bid_quantity=0.0` and `total_ask_quantity=0.0` to the test fixture, we ensure that the test reflects the current `MarketSignalDTO` structure and that the `PublicManager` can process these signals correctly without crashing.
This aligns with the "DTO Purity" guardrail, ensuring that typed DTOs are used correctly and consistently across the system.

## [Test Evidence]
```
tests/unit/modules/system/execution/test_public_manager_compliance.py::TestPublicManagerCompliance::test_implements_financial_agent PASSED [ 25%]
tests/unit/modules/system/execution/test_public_manager_compliance.py::TestPublicManagerCompliance::test_implements_asset_recovery_system PASSED [ 50%]
tests/unit/modules/system/execution/test_public_manager_compliance.py::TestPublicManagerCompliance::test_bankruptcy_processing_id_handling
-------------------------------- live log call ---------------------------------
WARNING  PublicManager:public_manager.py:92 Processing bankruptcy for Agent 99 at tick 1. Recovering inventory.
INFO     PublicManager:public_manager.py:100 Recovered 10.0 of gold.
PASSED                                                                   [ 75%]
tests/unit/modules/system/execution/test_public_manager_compliance.py::TestPublicManagerCompliance::test_liquidation_order_generation_id
-------------------------------- live log call ---------------------------------
INFO     PublicManager:public_manager.py:172 Generated liquidation order for 1.0 of gold at 95.0.
PASSED                                                                   [100%]

============================== 4 passed in 0.18s ===============================
```
