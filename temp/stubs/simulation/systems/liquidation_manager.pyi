from _typeshed import Incomplete
from modules.common.financial.dtos import Claim as Claim
from modules.finance.api import ILiquidatable, IShareholderRegistry as IShareholderRegistry, ITaxService as ITaxService
from modules.hr.api import IHRService as IHRService
from modules.system.api import CurrencyCode as CurrencyCode, IAgentRegistry as IAgentRegistry, IAssetRecoverySystem as IAssetRecoverySystem
from simulation.dtos.api import SimulationState as SimulationState
from simulation.finance.api import ISettlementSystem as ISettlementSystem
from simulation.firms import Firm as Firm
from simulation.models import Transaction as Transaction
from simulation.systems.liquidation_handlers import ILiquidationHandler as ILiquidationHandler, InventoryLiquidationHandler as InventoryLiquidationHandler

logger: Incomplete

class LiquidationManager:
    """
    Manages the liquidation waterfall process for insolvent firms.
    Implements TD-187 Protocol.
    Refactored to comply with SRP (WO-211) and TD-269 Protocol Purity.
    """
    settlement_system: Incomplete
    hr_service: Incomplete
    tax_service: Incomplete
    agent_registry: Incomplete
    shareholder_registry: Incomplete
    public_manager: Incomplete
    handlers: list[ILiquidationHandler]
    def __init__(self, settlement_system: ISettlementSystem, hr_service: IHRService, tax_service: ITaxService, agent_registry: IAgentRegistry, shareholder_registry: IShareholderRegistry, public_manager: IAssetRecoverySystem | None = None) -> None: ...
    def initiate_liquidation(self, agent: ILiquidatable, state: SimulationState) -> None:
        """
        Executes the liquidation waterfall.
        Refactored to use ILiquidatable protocol (TD-269).
        """
    def execute_waterfall(self, agent: ILiquidatable, claims: list[Claim], available_cash: float, state: SimulationState, other_assets: dict[CurrencyCode, float] = None) -> None:
        """
        Distributes cash according to tiers.
        TD-033: Added other_assets for Tier 5 distribution.
        """
