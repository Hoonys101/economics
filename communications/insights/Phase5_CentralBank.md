# Phase 5: Central Bank Service Implementation & Insights

**Mission**: Implement `CentralBankService` adhering to `ICentralBank` protocol (Phase 5).
**Status**: Implemented Service & Tests. API updated.

## 1. Implementation Details

- **Service**: `modules/finance/central_bank/service.py` created.
  - Implements `ICentralBank`.
  - Manages Policy Rate state.
  - Orchestrates Open Market Operations (OMO) by interacting with `ITreasuryService`.
- **API Updates**:
  - `modules/finance/central_bank/api.py`: `conduct_open_market_operation` now accepts `currency`.
  - `modules/government/treasury/api.py`: `execute_market_purchase` and `execute_market_sale` now accept `currency`.
  - These changes ensure **Multi-Currency Awareness** as requested.
- **Tests**: `tests/unit/modules/finance/central_bank/test_service.py` verifies logic and OMO delegation.

## 2. Technical Debt & Architectural Insights

### A. Dual Central Bank Logic
Currently, there is a split in responsibilities:
1.  **Legacy Agent (`simulation/agents/central_bank.py`)**:
    - Implements `ICurrencyHolder`.
    - Contains Taylor Rule logic (`calculate_rate`).
    - Manages `Wallet` directly.
    - Runs in the simulation loop (`step`).
2.  **New Service (`CentralBankService`)**:
    - Implements `ICentralBank`.
    - Provides a clean API for Rate Setting and OMO.
    - Designed to be a domain service, not a simulation agent.

**Insight**: The `CentralBank` agent should eventually utilize `CentralBankService` to execute its decisions. The Taylor Rule logic in the agent should result in a call to `CentralBankService.set_policy_rate()`.

### B. Treasury Service Dependency
The OMO logic relies on `ITreasuryService`.
- The interface for `ITreasuryService` was updated to support `currency`.
- **Action Required**: Any implementation of `ITreasuryService` must be updated to handle the `currency` parameter. Currently, no active implementation was found in the codebase (only interfaces and specs), so this risk is low, but future implementers must be aware.

### C. Bond Management
- The `CentralBank` agent currently holds a list of bonds (`self.bonds`).
- The `CentralBankService` OMO logic relies on `TreasuryService` to handle the actual exchange.
- **Future Work**: Ensure `TreasuryService` correctly updates the Central Bank's bond holdings (likely via `Registry` or `SettlementSystem`) when OMOs occur. The Service itself is stateless regarding the bond inventory.

### D. ID Management
- `CentralBankService` is initialized with `agent_id` (defaulting to `ID_CENTRAL_BANK = 0`).
- This aligns with `simulation/agents/central_bank.py` using the same ID.
