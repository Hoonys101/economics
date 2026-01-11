import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import create_simulation
from simulation.models import Order

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VERIFY_HOUSING")

# Enable debug for system2
logging.getLogger("simulation.ai.household_system2").setLevel(logging.DEBUG)

def verify():
    # Force single tick save to ensure DB isn't bottleneck (though we run in memory mostly)
    sim = create_simulation(overrides={"BATCH_SAVE_INTERVAL": 1})

    # Find a house owner
    owner = None
    for h in sim.households:
        if h.owned_properties:
            owner = h
            break

    if not owner:
        logger.error("No house owners found in initialization!")
        return

    logger.info(f"Target Agent: {owner.id}, Assets: {owner.assets}, Properties: {owner.owned_properties}")

    # Bankrupt them
    owner.assets = 10.0 # Way below distress threshold (~450)
    logger.info(f"Bankrupted Agent {owner.id} to {owner.assets}")

    # Run Tick
    logger.info("Running Tick 1...")
    sim.run_tick()

    # Check for SELL order
    # Orders are processed in run_tick.
    # If successful, the agent should have sold the house.
    # Or at least placed an order.
    # If sold, owned_properties should be empty (if buyer existed).
    # If not sold, check market for active orders.

    housing_market = sim.markets.get("housing")
    if not housing_market:
        logger.error("Housing market missing!")
        return

    sell_orders = []
    # Check sell orders in book
    for item_id, orders in housing_market.sell_orders.items():
        for o in orders:
            if o.agent_id == owner.id and o.order_type == "SELL":
                sell_orders.append(o)

    if sell_orders:
        logger.info(f"SUCCESS: Found Sell Order from Agent {owner.id}: {sell_orders[0]}")
    else:
        # Check if already sold (if match happened immediately)
        if not owner.owned_properties:
             logger.info(f"SUCCESS: Agent {owner.id} sold the house immediately!")
        else:
             logger.error(f"FAILURE: No sell order found and house still owned.")
             # Debug info
             logger.info(f"Agent Housing Target Mode: {getattr(owner, 'housing_target_mode', 'N/A')}")
             return # Abort if no sell order

    # Check Grace Period
    # If sold (or just moved out? No, grace period is triggered on Sell Transaction)
    # If order is pending, no grace period yet.

    # Force a buy to test Grace Period
    if sell_orders and owner.owned_properties:
        # Create a rich buyer
        buyer = sim.households[-1]
        if buyer.id == owner.id: buyer = sim.households[-2]

        buyer.assets = 1000000.0
        unit_id = sell_orders[0].item_id
        price = sell_orders[0].price

        logger.info(f"Rich Buyer {buyer.id} buying {unit_id} at {price}")
        buy_order = Order(
            agent_id=buyer.id,
            item_id=unit_id,
            price=price,
            quantity=1.0,
            market_id="housing",
            order_type="BUY"
        )
        sim.markets["housing"].place_order(buy_order, sim.time)

        # Run match (usually happens in run_tick, but we can force it or run next tick)
        logger.info("Running Tick 2 (Force Match)...")
        sim.run_tick()

        # Check ownership and grace period
        if not owner.owned_properties:
            logger.info(f"House sold! Owner Grace Period: {getattr(owner, 'housing_grace_period', -1)}")
            if owner.housing_grace_period > 0:
                logger.info("VERIFICATION PASSED: Grace Period Active.")
            else:
                logger.error(f"VERIFICATION FAILED: No Grace Period (Val={owner.housing_grace_period}).")
        else:
            logger.error("Transaction failed to clear.")

if __name__ == "__main__":
    verify()
