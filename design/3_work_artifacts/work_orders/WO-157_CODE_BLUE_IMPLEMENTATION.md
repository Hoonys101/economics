```markdown
# Work Order: WO-157 - Code Blue Deadlock Fixes

- **Mission Key**: `WO-157`
- **Objective**: Implement demand elasticity for Households and dynamic pricing for Firms to resolve the "Price-Consumption Deadlock" (TD-157) and create a self-correcting market mechanism.
- **Affected Components**:
    - `modules.household.econ_component.EconComponent`
    - `simulation.decisions.ai_driven_household_engine.AIDrivenHouseholdDecisionEngine`
    - `simulation.core_agents.Firm` (or equivalent producer agent)
    - `simulation.core_markets.BasicMarket`
    - `simulation.dtos.config_dtos`
    - `modules.household.dtos`
- **Responsible Scribe**: Gemini

---

## 1. Part 1: Household Demand Elasticity

### 1.1. Architectural Mandate & Locus of Change

As per the Pre-flight Audit (WO-157), the implementation **must not** modify the `Household.decide_and_consume` method, which handles inventory consumption. The logic for demand elasticity must be implemented within the **market purchasing workflow**, specifically within the `AIDrivenHouseholdDecisionEngine`, which is responsible for generating initial purchase orders.

### 1.2. Interface & DTO Modifications (`modules/household/api.py`)

#### 1.2.1. Add Elasticity to `SocialStateDTO`

To link purchasing behavior to personality, an elasticity factor will be added to the social state.

```python
# In modules/household/dtos.py

class SocialStateDTO(TypedDict):
    # ... existing fields
    demand_elasticity: float # New field
```

#### 1.2.2. New Config Parameters in `HouseholdConfigDTO`

New parameters will be added to `config/economy_params.yaml` and loaded into the `HouseholdConfigDTO`.

```python
# In simulation/dtos/config_dtos.py

class HouseholdConfigDTO(TypedDict):
    # ... existing fields
    elasticity_mapping: Dict[str, float] # e.g., {"MISER": 2.0, "IMPULSIVE": 0.5, "DEFAULT": 1.0}
    max_willingness_to_pay_multiplier: float # e.g., 2.5
```

### 1.3. Logic Implementation (Pseudo-code)

The core change will be within the `AIDrivenHouseholdDecisionEngine`'s decision-making process, likely in a method like `_generate_purchase_orders`. The current binary buy/no-buy logic will be replaced with a continuous quantity calculation.

```python
# In AIDrivenHouseholdDecisionEngine._generate_purchase_orders (Conceptual)

def _generate_purchase_orders(self, context: DecisionContext) -> List[Order]:
    orders = []
    
    # Extract relevant state from context DTOs
    needs = context.state.needs
    assets = context.state.assets
    perceived_prices = context.state.perceived_prices
    demand_elasticity = context.state.demand_elasticity # Sourced from SocialStateDTO
    
    # Get config values
    mwtp_multiplier = context.config.max_willingness_to_pay_multiplier

    # Iterate through goods the agent considers buying
    for good_id, good_info in context.goods_data.items():
        if self._should_consider_good(good_id, needs):
            
            # --- START: New Elasticity Logic ---

            base_need_urgency = needs.get(good_info["need_category"], 0.0)
            current_price = perceived_prices.get(good_id, good_info["initial_price"])

            # 1. Define Max Affordable Price: The price point at which demand drops to zero.
            # This is a proxy for the agent's absolute reservation price.
            max_affordable_price = mwtp_multiplier * perceived_prices.get(good_id, current_price)

            # 2. Handle Price Inversion: If current price > max affordable, quantity is zero.
            if current_price >= max_affordable_price:
                quantity_to_buy = 0.0
            else:
                # 3. Calculate Quantity using the Demand Curve formula
                # The 'base_need_urgency' acts as the demand ceiling.
                price_ratio = current_price / max_affordable_price
                quantity_to_buy = base_need_urgency * (1 - price_ratio)**demand_elasticity

            # 4. Enforce Budget Constraint (Zero-Sum Integrity)
            cost = quantity_to_buy * current_price
            if cost > assets:
                quantity_to_buy = assets / current_price # Buy what can be afforded
                cost = assets

            # --- END: New Elasticity Logic ---
            
            if quantity_to_buy > 0.01: # Threshold to avoid dust orders
                orders.append(Order(
                    agent_id=context.state.id,
                    good_id=good_id,
                    quantity=quantity_to_buy,
                    order_type="buy"
                ))
                # Update remaining assets for subsequent calculations in this tick
                assets -= cost
    
    return orders
```

---

## 2. Part 2: Firm Dynamic Pricing

### 2.1. Architectural Mandate

To break price rigidity, Firms must track sales velocity and reduce prices on stale inventory. This logic will reside in the `Firm` agent's `decide_pricing` method (or equivalent).

### 2.2. Interface & DTO Modifications (`modules/firm/api.py` - conceptual)

#### 2.2.1. State Tracking in `FirmStateDTO`

The `Firm` agent's state DTO must be updated to track inventory age.

```python
# In a conceptual modules/firm/dtos.py

class FirmStateDTO(TypedDict):
    # ... existing fields
    inventory_last_sale_tick: Dict[str, int] # Maps good_id to the tick of its last sale
```

#### 2.2.2. New Config Parameters

New parameters will be added to `config/economy_params.yaml`.

```yaml
# In economy_params.yaml
firm:
  sale_timeout_ticks: 20 # Ticks after which a price reduction is triggered
  dynamic_price_reduction_factor: 0.95 # e.g., 5% price drop
```

### 2.3. Logic Implementation (Pseudo-code)

The logic will be part of the Firm's periodic update cycle, likely before it posts offers to the market.

```python
# In Firm.decide_pricing (Conceptual)

def decide_pricing(self, current_tick: int):
    
    # Get config values
    timeout_ticks = self.config.sale_timeout_ticks
    reduction_factor = self.config.dynamic_price_reduction_factor

    new_prices = self.current_prices.copy()

    for good_id, inventory_item in self.inventory.items():
        if inventory_item.quantity > 0:
            last_sale_tick = self.state.inventory_last_sale_tick.get(good_id, 0)
            
            # Check if inventory is stale
            if (current_tick - last_sale_tick) > timeout_ticks:
                
                # Apply price reduction
                original_price = new_prices[good_id]
                new_price = original_price * reduction_factor
                
                # Ensure price doesn't drop below production cost
                production_cost = self.get_production_cost(good_id)
                new_prices[good_id] = max(new_price, production_cost)
                
                self.logger.info(f"Dynamic Pricing: Reduced price for {good_id} to {new_prices[good_id]}")

    self.current_prices = new_prices

# The Firm's `process_sale` method must be updated to record the transaction tick.
def process_sale(self, good_id: str, quantity: float, current_tick: int):
    # ... existing logic ...
    self.state.inventory_last_sale_tick[good_id] = current_tick
```

---

## 3. Verification Plan

1.  **Unit Tests (Household)**:
    - Create a test for the `_generate_purchase_orders` logic.
    - Use `pytest.mark.parametrize` to test different personalities (`demand_elasticity`), need levels, and asset levels.
    - **Golden Data**:
        - **Case 1 (Miser)**: High elasticity, low assets. Should buy a very small quantity at high prices.
        - **Case 2 (Impulsive)**: Low elasticity, high assets. Should buy a larger quantity even at moderately high prices.
        - **Case 3 (Priced Out)**: Agent with assets lower than `price`. Must purchase `0` quantity.
    - Assert that `quantity > 0` and that the total cost is within the agent's assets. Use `assertAlmostEqual` for float comparisons.

2.  **Unit Tests (Firm)**:
    - Create a test for the `decide_pricing` logic.
    - Manually advance the `current_tick` to simulate time passing without a sale.
    - **Golden Data**:
        - **Case 1 (Stale Inventory)**: `current_tick` is greater than `last_sale_tick + sale_timeout_ticks`. Assert that the price is reduced by the `dynamic_price_reduction_factor`.
        - **Case 2 (Fresh Inventory)**: `current_tick` is less than the timeout. Assert that the price remains unchanged.
        - **Case 3 (Floor Price)**: The calculated price reduction would go below production cost. Assert that the price is set exactly to the production cost.

3.  **Integration Test**:
    - A dedicated test scenario (`test_code_blue_deadlock_resolution`) will be created.
    - It will set up a market with one Firm and one Household in the deadlock condition (high price, no sales).
    - The test will run the simulation for `sale_timeout_ticks + 1` ticks.
    - **Assertion**: Verify that the Firm lowers its price and the Household successfully makes a purchase, breaking the deadlock.

## 4. Risk & Impact Audit (Mitigation Plan)

- **1. Architectural Constraint (Facade/Component Model)**:
    - **Mitigation**: This spec explicitly places the demand elasticity logic within the `AIDrivenHouseholdDecisionEngine` and the dynamic pricing logic within the `Firm` agent, adhering to the Facade-Component pattern. The `Household` class itself remains untouched.

- **2. Critical Risk (Incorrect Locus of Change)**:
    - **Mitigation**: This spec correctly targets the market **purchasing** workflow (`_generate_purchase_orders` in the `DecisionEngine`) instead of the **inventory consumption** workflow (`decide_and_consume`), directly addressing the primary risk identified by the audit.

- **3. Architectural Constraint (State Management via DTOs)**:
    - **Mitigation**: All new state variables (`demand_elasticity`, `inventory_last_sale_tick`) are added to their respective DTOs (`SocialStateDTO`, `FirmStateDTO`). The pseudo-code demonstrates sourcing all required data from the `DecisionContext` God Object, ensuring no direct state modification on the agent facades.

- **4. Critical Risk (Widespread Test Invalidation)**:
    - **Mitigation**: The Verification Plan mandates that new and existing tests will be updated to use range-based checks (`assertAlmostEqual`) instead of asserting exact purchase quantities. This acknowledges that behavior is now continuous, not discrete.

- **5. Hidden Dependency (`DecisionContext` God Object)**:
    - **Mitigation**: The design accepts this dependency as a necessary constraint of the current architecture. New state required for the decision (`demand_elasticity`) is passed through the existing `DecisionContext` by extending the `HouseholdStateDTO`. While not ideal, this avoids major refactoring of the `make_decision` signature across the codebase, containing the scope of the change.

---

## 5. Insight Logging Mandate

- **[Routine] Mandatory Reporting**: Upon implementation, any insights or unforeseen complexities encountered while implementing the continuous demand curve and its interaction with the AI's Q-table must be logged to `communications/insights/WO-157_demand_elasticity.md`. This includes challenges in balancing exploration with the new deterministic formula.
```
