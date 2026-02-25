from typing import List, Any, TYPE_CHECKING, Dict, Optional
import logging
from modules.system.api import DEFAULT_CURRENCY
from modules.simulation.api import InventorySlot
from modules.finance.utils.currency_math import round_to_pennies

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
    MIN_CAPITAL = 10_000_000  # 100,000.00 USD -> 10,000,000 pennies
    INITIAL_INVENTORY = 50.0  # Quantity is still float


    @staticmethod
    def distribute_initial_wealth(central_bank: Any, target_agent: Any, amount: int, settlement_system: Any) -> None:
        """
        Transfers initial wealth from Central Bank to target agent.
        Ensures zero-sum integrity via SettlementSystem.
        Phase 33: Uses create_and_transfer for Central Bank to ensure M2 Expansion is recorded.
        """
        amount_pennies = int(amount)
        if amount_pennies > 0:
             from modules.system.constants import ID_CENTRAL_BANK
             # Check if source is Central Bank
             is_cb = False
             if hasattr(central_bank, 'id'):
                 is_cb = str(central_bank.id) == str(ID_CENTRAL_BANK)

             if is_cb and hasattr(settlement_system, 'create_and_transfer'):
                 tx = settlement_system.create_and_transfer(central_bank, target_agent, amount_pennies, "GENESIS_GRANT", tick=0)
             else:
                 tx = settlement_system.transfer(central_bank, target_agent, amount_pennies, "GENESIS_GRANT")

             if tx is None:
                 raise KeyError(f"Failed to distribute wealth to Agent {target_agent.id}. Agent possibly not registered.")
             logger.debug(f"GENESIS_GRANT | Transferred {amount_pennies} to Agent {target_agent.id}")

    @staticmethod
    def force_assign_workers(firms: List['Firm'], households: List['Household']) -> int:
        MAX_FORCED_WORKERS = 5
        DEFAULT_WAGE = 5000 # 50.00 USD
        assigned_count = 0
        unemployed = [h for h in households if h._econ_state.employer_id is None and h._bio_state.is_active]

        for firm in firms:
            if not firm.is_active:
                continue
            if len(firm.hr_state.employees) == 0:
                workers_needed = min(MAX_FORCED_WORKERS, len(unemployed))
                for _ in range(workers_needed):
                    if not unemployed:
                        break
                    worker = unemployed.pop(0)
                    worker.employer_id = firm.id
                    worker.current_wage = DEFAULT_WAGE
                    # Use HR Engine directly
                    firm.hr_engine.hire(firm.hr_state, worker, DEFAULT_WAGE, 0) # Genesis Tick
                    assigned_count += 1
                logger.info(f'BOOTSTRAPPER | Force-assigned {workers_needed} workers to Firm {firm.id}')

        logger.info(f'BOOTSTRAPPER | Total force-assigned workers: {assigned_count}')
        return assigned_count
    @staticmethod
    def inject_liquidity_for_firm(firm: 'Firm', config: Any, settlement_system: Any, central_bank: Any, current_tick: int = 0) -> bool:
        """
        Injects liquidity (inputs and capital) for a single firm.
        Returns True if any resource was injected.

        Zero-Sum Compliance:
        - Capital is transferred from Central Bank.
        - Physical Goods (Inputs) are only magically created at Tick 0 (Genesis).
        """
        BUFFER_DAYS = 30.0
        injected = False

        # 1. Input Injection (Supply Side) - ONLY AT GENESIS
        if current_tick == 0:
            if firm.specialization in config.GOODS:
                item_config = config.GOODS[firm.specialization]

                if 'inputs' in item_config and item_config['inputs']:
                    for mat, qty_per_unit in item_config['inputs'].items():
                        needed = qty_per_unit * firm.production_target * BUFFER_DAYS
                        current = firm.get_quantity(mat, slot=InventorySlot.INPUT)
                        if current < needed:
                            firm.add_item(mat, needed - current, slot=InventorySlot.INPUT)
                            injected = True

                current_inv = firm.get_quantity(firm.specialization)
                if current_inv < Bootstrapper.INITIAL_INVENTORY:
                    needed = Bootstrapper.INITIAL_INVENTORY - current_inv
                    firm.add_item(firm.specialization, needed)
                    injected = True
                    logger.info(f'BOOTSTRAPPER | Injected {needed} units to Firm {firm.id} (Genesis)')

        # 2. Capital Injection (Demand Side) - ALWAYS ALLOWED (via Transfer)
        current_balance = firm.wallet.get_balance(DEFAULT_CURRENCY)
        if current_balance < Bootstrapper.MIN_CAPITAL:
            diff = round_to_pennies(Bootstrapper.MIN_CAPITAL - current_balance)
            if settlement_system and central_bank:
                from modules.system.constants import ID_CENTRAL_BANK
                is_cb = False
                if hasattr(central_bank, 'id'):
                    is_cb = str(central_bank.id) == str(ID_CENTRAL_BANK)

                if is_cb and hasattr(settlement_system, 'create_and_transfer'):
                    tx = settlement_system.create_and_transfer(central_bank, firm, diff, "BOOTSTRAP_INJECTION", tick=current_tick)
                else:
                    tx = settlement_system.transfer(central_bank, firm, diff, "BOOTSTRAP_INJECTION")

                if tx is None:
                    raise KeyError(f"Failed to inject liquidity to Firm {firm.id}. Agent possibly not registered.")
                logger.info(f"BOOTSTRAPPER | Injected {diff} capital to Firm {firm.id} via Settlement.")
                injected = True
            else:
                msg = f"BOOTSTRAPPER | Failed to inject {diff} to Firm {firm.id}. SettlementSystem or CentralBank missing."
                logger.critical(msg)
                raise RuntimeError(msg)

        return injected

    @staticmethod
    def inject_initial_liquidity(firms: List['Firm'], config: Any, settlement_system: Any = None, central_bank: Any = None) -> None:
        """
        Injects a 30-tick buffer of raw materials and minimum capital.
        """
        injected_count = 0

        for firm in firms:
            if Bootstrapper.inject_liquidity_for_firm(firm, config, settlement_system, central_bank, current_tick=0):
                injected_count += 1

        logger.info(f"BOOTSTRAPPER | Injected resources into {injected_count} firms.")
