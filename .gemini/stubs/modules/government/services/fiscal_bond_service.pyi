from _typeshed import Incomplete
from modules.finance.api import BondDTO as BondDTO
from modules.government.api import IFiscalBondService as IFiscalBondService
from modules.government.dtos import BondIssuanceResultDTO as BondIssuanceResultDTO, BondIssueRequestDTO as BondIssueRequestDTO, FiscalContextDTO as FiscalContextDTO, PaymentRequestDTO as PaymentRequestDTO
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY
from typing import Any

logger: Incomplete

class FiscalBondService(IFiscalBondService):
    """
    Stateless service responsible for sovereign debt logic:
    calculating yields, determining buyers (QE), and preparing issuance.
    """
    config_module: Incomplete
    def __init__(self, config_module: Any = None) -> None: ...
    def calculate_yield(self, context: FiscalContextDTO) -> float:
        """
        Calculates bond yield based on market conditions.
        """
    def issue_bonds(self, request: BondIssueRequestDTO, context: FiscalContextDTO, buyer_pool: dict[str, Any]) -> BondIssuanceResultDTO:
        """
        Prepares a bond issuance transaction.
        Determines the buyer (e.g. Central Bank vs Commercial Bank) and creates the transaction request.
        """
