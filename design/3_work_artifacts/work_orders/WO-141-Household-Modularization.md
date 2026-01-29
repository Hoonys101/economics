# Work Order: WO-141 - Household Engine Modularization

## 🎯 Objective
Refactor the monolithic `AIDrivenHouseholdDecisionEngine` (600+ LOC) in `simulation/decisions/ai_driven_household_engine.py` into a modularized coordinator-delegate pattern. This will separate concerns into specialized managers: Consumption, Labor, Asset, and Housing.

---

## 🛠️ Tasks

### 1. Create API and Manager Interfaces
- Create `simulation/decisions/household/api.py`.
- Define specific Context DTOs: `ConsumptionContext`, `LaborContext`, `AssetManagementContext`, `HousingContext`.
- Define Abstract Base Classes (Protocols) for all four managers.

### 2. Implement Specialized Managers
Create the following modules in `simulation/decisions/household/`:
- `consumption_manager.py`: Logic for purchasing goods, Maslow constraints, and hoarding/inflation psychology.
- `labor_manager.py`: Logic for job mobility, quit decisions, and reservation wage (including panic mode).
- `asset_manager.py`: Orchestrates portfolio management, liquidity checks, and stock trading.
- `stock_trader.py`: Specific execution of stock buy/sell orders.
- `housing_manager.py`: Use the existing logic to handle real estate mimicry and purchases.

### 3. Refactor HouseholdDecisionEngine (The Coordinator)
- Update `AIDrivenHouseholdDecisionEngine`:
    - Remove all direct decision logic.
    - Implement the coordinator pattern: fetch action vector -> shard context -> delegate to managers -> collect orders.
- Maintain the exact same external `ai_engine` interface.

### 4. Implementation of Behavioral Equivalence Test
- **CRITICAL**: Create `tests/decisions/test_household_engine_refactor.py`.
- Implement a test that runs both the `LegacyEngine` (copy of old code) and the `NewEngine` against identical complex contexts.
- Ensure 100% order-level parity.

---

## 🏗️ Technical Constraints
- **Zero-Sum / Purity Gate**: All managers must use DTOs only; no direct access to simulation objects.
- **Unidirectional Flow**: Managers must be stateless and have no upward dependencies.
- **Equivalence Target**: Any deviation in logic must be documented and explicitly approved; otherwise, 1 to 1 parity is required.

---

## 🏁 Success Sign-off
- [ ] `AIDrivenHouseholdDecisionEngine` LOC reduced to < 100 lines (coordinator logic only).
- [ ] Behavioral Equivalence Test passes for 10+ complex scenarios.
- [ ] New modular tests for each manager pass with 100% coverage.
- [ ] All DTO-Purity rules satisfied.
