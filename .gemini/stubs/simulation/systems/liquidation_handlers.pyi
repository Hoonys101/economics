import abc
from _typeshed import Incomplete
from abc import ABC, abstractmethod
from modules.finance.api import ILiquidatable as ILiquidatable
from modules.system.api import IAssetRecoverySystem as IAssetRecoverySystem
from simulation.dtos.api import SimulationState as SimulationState
from simulation.finance.api import ISettlementSystem as ISettlementSystem
from simulation.firms import Firm as Firm

logger: Incomplete

class ILiquidationHandler(ABC, metaclass=abc.ABCMeta):
    """
    Interface for asset-specific liquidation logic.
    """
    @abstractmethod
    def liquidate(self, agent: ILiquidatable, state: SimulationState) -> None:
        """
        Liquidates specific assets of the firm to generate cash.
        """

class InventoryLiquidationHandler(ILiquidationHandler):
    """
    Liquidates firm inventory by selling to PublicManager.
    """
    settlement_system: Incomplete
    public_manager: Incomplete
    def __init__(self, settlement_system: ISettlementSystem, public_manager: IAssetRecoverySystem) -> None: ...
    def liquidate(self, agent: ILiquidatable, state: SimulationState) -> None:
        """
        Liquidates non-cash assets (Inventory) by selling them to the PublicManager.
        This prevents the 'Asset-Rich Cash-Poor' leak.
        """
