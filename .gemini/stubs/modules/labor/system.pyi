from _typeshed import Incomplete
from modules.common.enums import IndustryDomain as IndustryDomain
from modules.labor.api import ILaborMarket as ILaborMarket, JobOfferDTO as JobOfferDTO, JobSeekerDTO as JobSeekerDTO, LaborConfigDTO as LaborConfigDTO, LaborMarketMatchResultDTO as LaborMarketMatchResultDTO
from modules.market.api import CanonicalOrderDTO as CanonicalOrderDTO, OrderTelemetrySchema as OrderTelemetrySchema
from modules.simulation.api import AgentID as AgentID
from simulation.interfaces.market_interface import IMarket
from simulation.models import Transaction
from typing import Any

logger: Incomplete

class LaborMarket(ILaborMarket, IMarket):
    """
    Implementation of the Labor Market with Major-Matching logic.
    """
    id: Incomplete
    config: Incomplete
    def __init__(self, market_id: str = 'labor', config_module: Any = None) -> None: ...
    def configure(self, config: LaborConfigDTO) -> None:
        """
        Injects configuration into the Labor Market.
        """
    def post_job_offer(self, offer: JobOfferDTO) -> None: ...
    def post_job_seeker(self, seeker: JobSeekerDTO) -> None: ...
    def match_market(self, current_tick: int) -> list[LaborMarketMatchResultDTO]: ...
    @property
    def buy_orders(self) -> dict[str, list[CanonicalOrderDTO]]: ...
    @property
    def sell_orders(self) -> dict[str, list[CanonicalOrderDTO]]: ...
    @property
    def matched_transactions(self) -> list[Transaction]: ...
    def get_daily_avg_price(self) -> float: ...
    def get_daily_volume(self) -> float: ...
    def get_price(self, item_id: str) -> float: ...
    def cancel_orders(self, agent_id: str) -> None: ...
    def place_order(self, order_dto: CanonicalOrderDTO, current_time: int) -> list[Transaction]:
        """
        Adapter: CanonicalOrderDTO -> JobOffer/JobSeeker
        """
    def match_orders(self, current_time: int) -> list[Transaction]:
        """
        Executes matching and returns Transactions (HIRE type).
        """
    def clear_orders(self) -> None: ...
    def get_telemetry_snapshot(self) -> list[OrderTelemetrySchema]: ...
    def get_total_demand(self) -> float:
        """Returns total demand (job offers)."""
    def get_total_supply(self) -> float:
        """Returns total supply (job seekers)."""
