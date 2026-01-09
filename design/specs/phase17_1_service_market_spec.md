# Phase 17-1: Service Market (The Protocol of Time)

**Objective**: Implement the **Service Market**, where production is time-bound and cannot be stored (Perishability).
**Target Modules**: `simulation/firms.py`, `simulation/ai/firm_ai.py`, `config.py`

---

## 1. Concept: The Economics of Time
Unlike goods, Services are produced and consumed instantly.
- **Good**: Produced -> Inventory -> Sold -> Consumed.
- **Service**: Capacity Defined -> Sold (Produced) -> Consumed. (Unsold Capacity = Waste).

To integrate this into our discrete tick-based simulation:
1.  **Start of Tick**: Firm defines `Capacity` (Potential Production).
2.  **Market Phase**: Orders are matched. Sold capacity is "realized".
3.  **End of Tick**: Unsold capacity is **voided** (Inventory reset to 0). It does not carry over.

---

## 2. Class: `ServiceFirm` (The Body)
Inherits from `Firm`.

### 2.1 Logic Changes
- **`produce(current_time)`**:
    - Calculates `capacity` using the Production Function (same as Goods).
    - **Key Difference**: Sets `self.inventory[specialization] = capacity`.
    - *Note*: This is "Potential Inventory". If not sold, it vanishes.
- **`update_needs(current_time)`**:
    - **Void Logic**:
        - Calculates `unsold_inventory = self.inventory[specialization]`.
        - Records `waste = unsold_inventory`.
        - Sets `self.inventory[specialization] = 0.0`. (Manual Voiding).
    - **Cost Accounting**:
        - Unsold capacity still incurred `Wages` and `Capital Depreciation`.
        - This naturally simulates the high fixed cost / low variable cost nature of services.

### 2.2 New Attributes
- `capacity_this_tick`: Tracked for AI state.
- `sales_this_tick`: Tracked for AI state.
- `waste_this_tick`: Tracked for AI reward penalty.

---

## 3. Class: `ServiceFirmAI` (The Brain)
Inherits from `FirmAI` to fix the "Zero Inventory Panic" bug.

### 3.1 State Representation Issues
Existing `FirmAI` uses `Inventory Level` (Inventory / Target).
- For Service Firm, Inventory is wiped to 0 every tick.
- AI sees "0 Inventory" -> Panic -> Maximize Production -> Infinite Waste -> Bankruptcy.

### 3.2 Solution: Utilization-Based State
Override `_get_common_state` to replace **Inventory Metric** with **Utilization Metric**.

- **Metric**: `Utilization Rate` = `Sales / Capacity` (Last Tick).
- **Discretization**:
    - 0.0 - 0.5 (Under-utilized) -> Should Reduce Capacity (Fire/Sell Capital).
    - 0.5 - 0.9 (Healthy).
    - 0.9 - 1.0 (Over-utilized) -> Should Expand (Hire/Invest).

### 3.3 Reward Function Updates
Override `calculate_reward`.
- **Add Penalty**: `Waste Penalty`.
- $Reward = NetProfit - (Waste \times UnitCost \times 0.5)$
- *Reasoning*: Pure profit signal is too slow. Explicitly penalizing waste teaches the AI to match Demand perfectly (Just-in-Time).

---

## 4. Sector Implementation: Education
- **Product**: `service.education`
- **Need**: Satisfies `SELF_ACTUALIZATION` (Maslow) or `EDUCATION` need.
- **Effect**: Consumption increases `Household.labor_skill`.
    - *Implementation detail*: `Household.consume()` will check if item is `service.education` and apply logic: `self.labor_skill += 0.01 * quality`.

---

## 5. Verification Plan
### 5.1 Test: `verify_service_market.py`
Run a 100-tick simulation with a `ServiceFirm` and `ServiceFirmAI`.
- **Check 1: Perishability**: Verify `inventory` is 0.0 at the start of every tick.
- **Check 2: AI Adaptation**:
    - Start with Over-capacity (100 capacity, 10 demand).
    - Verify AI fires employees/sells capital to lower capacity.
    - Start with Under-capacity (10 capacity, 100 demand).
    - Verify AI hires to match demand.
- **Check 3: Solvency**: The firm should not go bankrupt within 100 ticks.

---

## 6. Definitions (Constants)
- `SERVICE_SECTORS`: `["service.education", "service.medical"]`
- `SERVICE_WASTE_PENALTY_FACTOR`: `0.5`
