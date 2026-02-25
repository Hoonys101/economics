from _typeshed import Incomplete
from modules.government.engines.api import FiscalConfigDTO as FiscalConfigDTO, FiscalDecisionDTO as FiscalDecisionDTO, FiscalRequestDTO as FiscalRequestDTO, FiscalStateDTO as FiscalStateDTO, GrantedBailoutDTO as GrantedBailoutDTO, IFiscalEngine as IFiscalEngine
from modules.system.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY, MarketSnapshotDTO as MarketSnapshotDTO
from typing import Any

logger: Incomplete

class FiscalEngine(IFiscalEngine):
    """
    Stateless engine that decides on government fiscal policy actions.
    Implements Taylor Rule for tax adjustments and evaluates bailout requests.
    Enforces Solvency Guardrails (Debt Brake, Bailout Limits).
    """
    config_dto: Incomplete
    def __init__(self, config_module: FiscalConfigDTO | Any = None) -> None: ...
    def decide(self, state: FiscalStateDTO, market: MarketSnapshotDTO, requests: list[FiscalRequestDTO]) -> FiscalDecisionDTO: ...
