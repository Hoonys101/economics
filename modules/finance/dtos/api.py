from dataclasses import dataclass
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

@dataclass(frozen=True)
class MoneySupplyDTO:
    """DTO for strictly segregated M2 and Debt aggregations."""
    m2_supply: int
    system_debt: int
    currency: CurrencyCode = DEFAULT_CURRENCY

@dataclass(frozen=True)
class BondIssuanceResultDTO:
    """Result of attempting to issue treasury bonds."""
    success: bool
    amount_issued: int
    reason: str = "SUCCESS"
