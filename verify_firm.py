import sys
import logging
from unittest.mock import MagicMock
from simulation.firms import Firm
from modules.simulation.api import AgentCoreConfigDTO
from modules.simulation.dtos.api import FirmConfigDTO

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Verification")

    # Mocks
    core_config = MagicMock(spec=AgentCoreConfigDTO)
    core_config.id = "FIRM_1"
    core_config.name = "Test Firm"
    core_config.logger = logger
    core_config.memory_interface = MagicMock()
    core_config.value_orientation = "PROFIT"
    core_config.initial_needs = {}

    engine = MagicMock()

    firm_config = MagicMock(spec=FirmConfigDTO)
    firm_config.firm_min_production_target = 100.0
    firm_config.ipo_initial_shares = 1000.0
    firm_config.dividend_rate = 0.1
    firm_config.profit_history_ticks = 10

    # Instantiate
    try:
        firm = Firm(
            core_config=core_config,
            engine=engine,
            specialization="FOOD",
            productivity_factor=1.0,
            config_dto=firm_config,
            initial_inventory={"WHEAT": 50.0}
        )
        logger.info("Firm instantiated successfully.")
    except Exception as e:
        logger.error(f"Failed to instantiate Firm: {e}")
        sys.exit(1)

    # Test Delegation
    firm.add_item("WOOD", 10.0)
    qty = firm.get_quantity("WOOD")
    if qty == 10.0:
        logger.info("Inventory delegation working.")
    else:
        logger.error(f"Inventory delegation failed. Expected 10.0, got {qty}")
        sys.exit(1)

    # Test Input Inventory Delegation
    from modules.simulation.api import InventorySlot
    firm.add_item("IRON", 5.0, slot=InventorySlot.INPUT)
    input_qty = firm.get_quantity("IRON", slot=InventorySlot.INPUT)
    if input_qty == 5.0:
        logger.info("Input Inventory delegation working.")
    else:
        logger.error(f"Input Inventory delegation failed. Expected 5.0, got {input_qty}")
        sys.exit(1)

    # Test Initial Inventory
    wheat_qty = firm.get_quantity("WHEAT")
    if wheat_qty == 50.0:
        logger.info("Initial inventory working.")
    else:
        logger.error(f"Initial inventory failed. Expected 50.0, got {wheat_qty}")
        sys.exit(1)

    firm.deposit(1000)
    bal = firm.get_balance()
    if bal == 1000:
        logger.info("Financial delegation working.")
    else:
        logger.error(f"Financial delegation failed. Expected 1000, got {bal}")
        sys.exit(1)

    logger.info("Verification passed.")

if __name__ == "__main__":
    main()
