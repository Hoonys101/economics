from typing import List, Any, TYPE_CHECKING, Dict
import logging

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.households import Household

logger = logging.getLogger(__name__)


class Bootstrapper:
    """
    System responsible for initializing agents with necessary resources
    to prevent 'Deadlock at Birth' scenarios.

    Ref: WO-058 Economic CPR
    """

    MIN_CAPITAL = 100_000.0  # Increased from 2000
    INITIAL_INVENTORY = 50.0  # New constant

    @staticmethod
    def force_assign_workers(firms: List["Firm"], households: List["Household"]) -> int:
        MAX_FORCED_WORKERS = 5
        DEFAULT_WAGE = 50.0
        assigned_count = 0
        unemployed = [h for h in households if h.employer_id is None and h.is_active]

        for firm in firms:
            if not firm.is_active:
                continue
            if len(firm.hr.employees) == 0:
                workers_needed = min(MAX_FORCED_WORKERS, len(unemployed))
                for _ in range(workers_needed):
                    if not unemployed:
                        break
                    worker = unemployed.pop(0)
                    worker.employer_id = firm.id
                    worker.wage = DEFAULT_WAGE
                    firm.hr.hire(worker, DEFAULT_WAGE)
                    assigned_count += 1
                logger.info(
                    f"BOOTSTRAPPER | Force-assigned {workers_needed} workers to Firm {firm.id}"
                )

        logger.info(f"BOOTSTRAPPER | Total force-assigned workers: {assigned_count}")
        return assigned_count

    @staticmethod
    def inject_initial_liquidity(firms: List["Firm"], config: Any) -> None:
        """
        Injects a 30-tick buffer of raw materials and minimum capital.

        Args:
            firms: List of Firm agents.
            config: Configuration module (contains GOODS definition).
        """
        BUFFER_DAYS = 30.0

        injected_count = 0

        for firm in firms:
            # 1. Input Injection (Supply Side)
            if firm.specialization in config.GOODS:
                item_config = config.GOODS[firm.specialization]

                # Check if this good requires inputs
                if "inputs" in item_config and item_config["inputs"]:
                    for mat, qty_per_unit in item_config["inputs"].items():
                        # Calculate needed amount: Qty * Target * Days
                        needed = qty_per_unit * firm.production_target * BUFFER_DAYS

                        # Update Inventory
                        current = firm.input_inventory.get(mat, 0.0)
                        if current < needed:
                            firm.input_inventory[mat] = needed
                            injected_count += 1

                # After existing logic, add:
                current_inv = firm.inventory.get(firm.specialization, 0.0)
                if current_inv < Bootstrapper.INITIAL_INVENTORY:
                    firm.inventory[firm.specialization] = Bootstrapper.INITIAL_INVENTORY
                    logger.info(
                        f"BOOTSTRAPPER | Injected {Bootstrapper.INITIAL_INVENTORY} units to Firm {firm.id}"
                    )

            # 2. Capital Injection (Demand Side)
            if firm.assets < Bootstrapper.MIN_CAPITAL:
                diff = Bootstrapper.MIN_CAPITAL - firm.assets
                firm._add_assets(diff)

        logger.info(f"BOOTSTRAPPER | Injected resources into {injected_count} firms.")
