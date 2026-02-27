import logging
from _typeshed import Incomplete
from modules.finance.api import IFinancialEntity as IFinancialEntity, IShareholderRegistry as IShareholderRegistry
from modules.simulation.api import IEstateRegistry as IEstateRegistry
from modules.system.api import IAssetRecoverySystem as IAssetRecoverySystem
from simulation.dtos.api import SimulationState as SimulationState
from simulation.finance.api import ISettlementSystem as ISettlementSystem
from simulation.interfaces.market_interface import IMarket as IMarket
from simulation.models import Transaction as Transaction
from simulation.systems.inheritance_manager import InheritanceManager as InheritanceManager
from simulation.systems.lifecycle.api import DeathConfigDTO as DeathConfigDTO, IDeathSystem as IDeathSystem
from simulation.systems.liquidation_manager import LiquidationManager as LiquidationManager

class DeathSystem(IDeathSystem):
    """
    Handles agent death, liquidation of assets, and inheritance processing.
    Refactored for Protocol Purity and Integer Math.
    """
    config: Incomplete
    inheritance_manager: Incomplete
    liquidation_manager: Incomplete
    settlement_system: Incomplete
    public_manager: Incomplete
    logger: Incomplete
    estate_registry: Incomplete
    def __init__(self, config: DeathConfigDTO, inheritance_manager: InheritanceManager, liquidation_manager: LiquidationManager, settlement_system: ISettlementSystem, public_manager: IAssetRecoverySystem, logger: logging.Logger, estate_registry: IEstateRegistry | None = None) -> None: ...
    def execute(self, state: SimulationState) -> list[Transaction]:
        """
        Executes the death phase.
        1. Firm Liquidation (Bankruptcy)
        2. Household Liquidation (Death & Inheritance)
        """
