from typing import List, Any, TYPE_CHECKING, Dict
import logging

if TYPE_CHECKING:
    from simulation.firms import Firm

logger = logging.getLogger(__name__)

class Bootstrapper:
    """
    System responsible for initializing agents with necessary resources
    to prevent 'Deadlock at Birth' scenarios.

    Ref: WO-058 Economic CPR
    """

    @staticmethod
    def inject_initial_liquidity(firms: List['Firm'], config: Any) -> None:
        """
        Injects a 30-tick buffer of raw materials and minimum capital.

        Args:
            firms: List of Firm agents.
            config: Configuration module (contains GOODS definition).
        """
        BUFFER_DAYS = 30.0
        MIN_CAPITAL = 2000.0  # Safe buffer for ~1 month of wages

        injected_count = 0

        for firm in firms:
            # 1. Input Injection (Supply Side)
            if firm.specialization in config.GOODS:
                item_config = config.GOODS[firm.specialization]

                # Check if this good requires inputs
                if 'inputs' in item_config and item_config['inputs']:
                    for mat, qty_per_unit in item_config['inputs'].items():
                        # Calculate needed amount: Qty * Target * Days
                        needed = qty_per_unit * firm.production_target * BUFFER_DAYS

                        # Update Inventory
                        current = firm.input_inventory.get(mat, 0.0)
                        if current < needed:
                            firm.input_inventory[mat] = needed
                            injected_count += 1

            # 2. Capital Injection (Demand Side)
            if firm.assets < MIN_CAPITAL:
                firm.assets = MIN_CAPITAL

        logger.info(f"BOOTSTRAPPER | Injected resources into {injected_count} firms.")
