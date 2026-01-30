# SPECIFICATION: Agent Survival & Valuation (SPEC_ANIMAL_PHASE2_AGENTS)

**Objective**: This specification details the implementation of agent-level survival and valuation logic, as a focused subset of the broader "Animal Spirits" initiative. It equips agents with more robust, autonomous economic behaviors to enhance market stability and realism, specifically by introducing survival instincts for households and more dynamic pricing strategies for firms. This document explicitly addresses the risks and constraints identified in the `AUTO-AUDIT FINDINGS`.

---

## 1. DTO & Interface Definitions

This logic is entirely dependent on system-level data structures being passed into the agent's decision context. Agents **MUST NOT** calculate this data themselves; they are pure consumers of the provided signals.

### 1.1. Core Signal DTO

The following DTO is calculated by a system-level observer and made available to agents.

```python
# To be defined in: modules/system/api.py
from typing import TypedDict, List, Optional

class MarketSignalDTO(TypedDict):
    """
    Provides agents with essential, pre-calculated signals about a specific market's state.
    This is passed within the MarketSnapshotDTO to maintain data purity.
    """
    market_id: str
    item_id: str
    best_bid: Optional[float]
    best_ask: Optional[float]
    last_traded_price: Optional[float]
    last_trade_tick: int # Tick of the last trade
    price_history_7d: List[float] # Rolling 7-tick price history
    volatility_7d: float # Standard deviation of price_history_7d
    order_book_depth_buy: int # Number of buy orders
    order_book_depth_sell: int # Number of sell orders
    is_frozen: bool # True if circuit breaker is active
```

### 1.2. Modified Context DTOs

The existing context DTOs are modified to include the new signals.

```python
# To be defined in: modules/system/api.py or relevant core DTO files

class MarketSnapshotDTO(TypedDict):
    """
    [MODIFIED] A snapshot of all relevant market data for a given tick.
    Now includes the new MarketSignalDTO.
    """
    tick: int
    market_data: Dict[str, Any] # Legacy market data, to be deprecated
    market_signals: Dict[str, MarketSignalDTO] # item_id -> signal_dto

class DecisionContext(TypedDict):
    """
    [MODIFIED] The complete context provided to a decision engine.
    The market_snapshot field is updated to the new structure.
    """
    state: "HouseholdStateDTO" # or FirmStateDTO
    config: "HouseholdConfigDTO" # or FirmConfigDTO
    goods_data: List[Dict[str, Any]]
    market_snapshot: MarketSnapshotDTO
    current_time: int
    # ... other existing fields
```

---

## 2. Household Survival Override

This logic allows households to prioritize survival needs above all else, preventing death by starvation when they have the means to purchase food.

- **Location**: `modules.household.decisions.AIDrivenHouseholdDecisionEngine.make_decisions`
- **Architectural Constraint**: This logic **MUST** be implemented as a preemptive check within the decision engine, before the standard, more complex decision-making flow is initiated. It **MUST NOT** be added to the `Household` state model itself.
- **Trigger**: Before standard decision-making, check if `state.needs['survival'] > config.survival_need_emergency_threshold`.

### 2.1. Logic (Pseudo-code)

```python
# In AIDrivenHouseholdDecisionEngine.make_decisions(self, context: DecisionContext)

survival_need = context.state.needs.get('survival', 0)
emergency_threshold = context.config.survival_need_emergency_threshold
food_id = context.config.primary_survival_good_id # e.g., "food"

if survival_need > emergency_threshold:
    # --- SURVIVAL OVERRIDE ACTIVATED ---
    self.logger.warning(f"SURVIVAL_OVERRIDE: Agent {context.state.id} has critical survival need: {survival_need}")

    # 1. Find the cheapest available food using the provided signal
    market_signal = context.market_snapshot.market_signals.get(food_id)
    
    if market_signal and market_signal['best_ask'] is not None:
        ask_price = market_signal['best_ask']
        
        # 2. Check affordability
        if context.state.assets >= ask_price:
            
            # 3. Create an aggressive BUY order to ensure fulfillment.
            # Bid slightly above the ask price to jump the queue.
            bid_price = ask_price * (1 + context.config.survival_bid_premium)
            quantity_to_buy = 1.0 # Buy a single unit to satisfy immediate need
            
            survival_order = Order(
                agent_id=context.state.id,
                item_id=food_id,
                order_type="BUY",
                quantity=quantity_to_buy,
                price=bid_price
            )
            
            self.logger.warning(f"SURVIVAL_ACTION: Agent {context.state.id} placing aggressive bid for {food_id} at {bid_price}.")
            
            # Return ONLY the survival order, skipping all other decisions for this tick.
            return [survival_order], ("SURVIVAL_PURCHASE", "MAX_PRIORITY")
        else:
            self.logger.error(f"SURVIVAL_FAILURE: Agent {context.state.id} cannot afford food at price {ask_price}.")
    else:
        self.logger.error(f"SURVIVAL_FAILURE: Agent {context.state.id} found no food available for sale.")
            
# If override is not triggered or cannot be executed, proceed to normal decision logic.
return self.run_normal_decision_flow(context)
```

---

## 3. Firm Pricing Logic: Cost-Plus & Fire-Sale

This provides firms with robust pricing strategies for situations with high uncertainty or financial distress.

- **Location**: `modules.firm.decisions.AIDrivenFirmDecisionEngine`
- **Architectural Constraint**: This logic **MUST** be implemented within the decision engine, either as a fallback or a supplement to the main pricing strategy. It **MUST NOT** be added to the `Firm` state model.

### 3.1. Cost-Plus Fallback (Pseudo-code)

This logic is used when placing SELL orders if market price signals are unreliable or stale.

```python
# In AIDrivenFirmDecisionEngine, within the logic for setting a sell price

def get_sell_price(self, item_id: str, context: DecisionContext) -> float:
    market_signal = context.market_snapshot.market_signals.get(item_id)
    production_cost = self.calculate_unit_cost(item_id, context.state) # Assumes this helper exists

    # 1. Determine if the market signal is unreliable
    is_unreliable = (
        market_signal is None or 
        market_signal['last_traded_price'] is None or
        (context.current_time - market_signal['last_trade_tick']) > context.config.max_price_staleness_ticks
    )

    if is_unreliable:
        # --- COST-PLUS FALLBACK ACTIVATED ---
        target_margin = context.config.default_target_margin
        sell_price = production_cost * (1 + target_margin)
        self.logger.info(f"COST_PLUS_PRICING: Firm {context.state.id} using cost-plus for {item_id}: {sell_price}")
        return sell_price
    else:
        # --- NORMAL MARKET-FOLLOWING LOGIC ---
        # (Example: use last traded price with a dynamic margin)
        dynamic_margin = self.calculate_dynamic_margin(context)
        sell_price = market_signal['last_traded_price'] * (1 + dynamic_margin)
        return sell_price

# ... later ...
# sell_price = self.get_sell_price(item_id, context)
# create_sell_order(item_id, sell_price, ...)
```

### 3.2. Fire-Sale Logic (Pseudo-code)

This logic generates additional, discounted SELL orders when the firm is in financial distress. This runs *after* primary orders for the tick have been decided.

```python
# In AIDrivenFirmDecisionEngine.make_decisions, after primary orders are generated

primary_orders = self.generate_primary_orders(context)
fire_sale_orders = []

# 1. Check for financial distress conditions
is_distressed = (
    context.state.assets < context.config.fire_sale_asset_threshold and
    any(inv > context.config.fire_sale_inventory_threshold for inv in context.state.inventory.values())
)

if is_distressed:
    self.logger.warning(f"FIRE_SALE: Firm {context.state.id} is in financial distress. Initiating fire sale.")
    
    for item_id, quantity in context.state.inventory.items():
        if quantity > context.config.fire_sale_inventory_target:
            # --- FIRE-SALE FOR SPECIFIC ITEM ---
            market_signal = context.market_snapshot.market_signals.get(item_id)
            production_cost = self.calculate_unit_cost(item_id, context.state)

            # 2. Determine a steep discount price
            if market_signal and market_signal['best_bid'] is not None:
                # Undercut the highest buyer to guarantee a quick sale
                fire_sale_price = market_signal['best_bid'] * (1 - context.config.fire_sale_discount)
            else:
                # No buyers, fall back to a discount on our own production cost
                fire_sale_price = production_cost * (1 - context.config.fire_sale_cost_discount)
            
            # Ensure price is not negative or zero
            fire_sale_price = max(0.01, fire_sale_price)

            # 3. Create order to sell off excess inventory
            quantity_to_sell = quantity - context.config.fire_sale_inventory_target
            
            fire_sale_order = Order(
                agent_id=context.state.id,
                item_id=item_id,
                order_type="SELL",
                quantity=quantity_to_sell,
                price=fire_sale_price
            )
            fire_sale_orders.append(fire_sale_order)
            self.logger.warning(f"FIRE_SALE_ORDER: Firm {context.state.id} selling {quantity_to_sell} of {item_id} at {fire_sale_price}")

return primary_orders + fire_sale_orders, ("FIRE_SALE", "HIGH_PRIORITY")
```

---

## 4. Verification Plan

1.  **Unit Tests**:
    -   `TestHouseholdSurvivalOverride`:
        -   **Scenario**: Simulate a household with a `survival` need above the emergency threshold and sufficient assets.
        -   **Assert**: Verify it returns exactly one `BUY` order for the primary survival good, with a price higher than the market `best_ask`. Verify it ignores all other potential actions.
        -   **Scenario**: Household has critical need but insufficient assets.
        -   **Assert**: Verify no order is created and an error is logged.
    -   `TestFirmPricingLogic`:
        -   **Scenario (Cost-Plus)**: Provide a `DecisionContext` where the `MarketSignalDTO` for a product is missing or its `last_trade_tick` is very old.
        -   **Assert**: Verify the firm's calculated sell price is exactly `production_cost * (1 + default_target_margin)`.
        -   **Scenario (Fire-Sale)**: Simulate a firm with assets below `fire_sale_asset_threshold` and inventory above `fire_sale_inventory_threshold`.
        -   **Assert**: Verify the decision engine returns its normal orders PLUS an additional, steeply discounted `SELL` order for the excess inventory.

2.  **CRITICAL: Golden Fixture Regeneration**:
    -   **Acknowledgement**: The implementation of this specification **WILL INVALIDATE** the economic outcomes of nearly all existing golden fixture tests. The fundamental agent behaviors are being altered.
    -   **Mandatory Action**: The project plan **MUST** include a dedicated work item for a full regeneration of all golden fixtures. This involves:
        1.  Running `scripts/fixture_harvester.py` and `scripts/generate_golden_fixtures.py` after implementation is complete.
        2.  Manually reviewing the new baseline simulation results to ensure they represent a sane and stable new economic equilibrium.

---

## 5. Risk & Impact Audit (Response to Pre-flight Check)

This specification is designed to explicitly comply with the constraints identified in the pre-flight audit.

-   **1. Dependency on `MarketSignalDTO`**: **(Acknowledged & Addressed)** Section 1 of this spec defines the required DTOs. The pseudo-code in Sections 2 & 3 demonstrates that agent logic purely consumes this data from the `DecisionContext` and performs no direct market calculations, thus maintaining architectural purity.

-   **2. Architectural Constraint (SRP)**: **(Acknowledged & Addressed)** The "Location" and "Architectural Constraint" directives in Sections 2 & 3 explicitly mandate that all new logic be implemented within the `AIDriven...DecisionEngine` classes. The design preempts or supplements the normal decision flow, correctly separating the "brain" (engine) from the "body" (state model).

-   **3. Systemic Risk (Test Invalidation)**: **(Acknowledged & Addressed)** Section 4.2 of the Verification Plan contains a critical notice acknowledging the widespread test invalidation. It makes the full regeneration and review of golden fixtures a mandatory, explicit part of the work plan.

-   **4. Hidden Dependencies**: **(Acknowledged & Addressed)** This specification focuses solely on agent-level logic. However, it is designed with the explicit assumption that it operates within an environment where other systemic stabilizers are active. Its success relies on:
    -   A **relaxed circuit breaker** at genesis to allow for initial price discovery.
    -   A **Public Manager** or similar system-level service to preserve asset value after bankruptcies, preventing deflationary spirals.
    These are considered external dependencies on the simulation environment that enable this agent logic to function as intended.
