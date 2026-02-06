from typing import List, Any, TYPE_CHECKING, Dict
import logging
from modules.system.api import DEFAULT_CURRENCY

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
    def distribute_initial_wealth(central_bank: Any, target_agent: Any, amount: float, settlement_system: Any) -> None:
        """
        Transfers initial wealth from Central Bank to target agent.
        Ensures zero-sum integrity via SettlementSystem.
        """
        if amount > 0:
             settlement_system.transfer(central_bank, target_agent, amount, "GENESIS_GRANT")
             logger.debug(f"GENESIS_GRANT | Transferred {amount:.2f} to Agent {target_agent.id}")

    @staticmethod
    def force_assign_workers(firms: List['Firm'], households: List['Household']) -> int:
        MAX_FORCED_WORKERS = 5
        DEFAULT_WAGE = 50.0
        assigned_count = 0
        unemployed = [h for h in households if h._econ_state.employer_id is None and h._bio_state.is_active]

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
                    firm.hr.hire(worker, DEFAULT_WAGE, 0) # Genesis Tick
                    assigned_count += 1
                logger.info(f'BOOTSTRAPPER | Force-assigned {workers_needed} workers to Firm {firm.id}')

        logger.info(f'BOOTSTRAPPER | Total force-assigned workers: {assigned_count}')
        return assigned_count

    @staticmethod
    def inject_initial_liquidity(firms: List['Firm'], config: Any, settlement_system: Any = None, central_bank: Any = None) -> None:
        """
        Injects a 30-tick buffer of raw materials and minimum capital.

        Args:
            firms: List of Firm agents.
            config: Configuration module (contains GOODS definition).
            settlement_system: System for financial transfers (WO-124).
            central_bank: Source of liquidity (WO-124).
        """
        BUFFER_DAYS = 30.0

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

                # After existing logic, add:
                current_inv = firm.get_quantity(firm.specialization)
                if current_inv < Bootstrapper.INITIAL_INVENTORY:
                    needed = Bootstrapper.INITIAL_INVENTORY - current_inv
                    firm.add_item(firm.specialization, needed)
                    logger.info(f'BOOTSTRAPPER | Injected {needed} units to Firm {firm.id}')


            # 2. Capital Injection (Demand Side)
            # Refactor: Use finance.balance
            current_balance = firm.finance.balance.get(DEFAULT_CURRENCY, 0.0)
            if current_balance < Bootstrapper.MIN_CAPITAL:
                diff = Bootstrapper.MIN_CAPITAL - current_balance
                if settlement_system and central_bank:
                    settlement_system.transfer(central_bank, firm, diff, "BOOTSTRAP_INJECTION")
                    logger.info(f"BOOTSTRAPPER | Injected {diff:.2f} capital to Firm {firm.id} via Settlement.")
                else:
                    # Fallback (Should not be used in Genesis mode, but keeps compatibility)
                    # Use finance.credit explicitly
                    firm.finance.credit(diff, "Legacy Bootstrap", currency=DEFAULT_CURRENCY)
                    logger.warning(f"BOOTSTRAPPER | Legacy injection of {diff:.2f} to Firm {firm.id} (No SettlementSystem).")

        logger.info(f"BOOTSTRAPPER | Injected resources into {injected_count} firms.")
