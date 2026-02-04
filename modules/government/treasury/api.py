# --- modules/government/treasury/api.py ---
from __future__ import annotations
from typing import Protocol, TypedDict, Literal, List
from dataclasses import dataclass
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

# ==============================================================================
# Data Transfer Objects (DTOs)
# ==============================================================================

@dataclass
class BondDTO:
    """
    Data Transfer Object for government bonds.
    Duplicate of the definition in modules/finance/api.py to support the new Treasury module.
    """
    id: str
    issuer: str
    face_value: float
    yield_rate: float
    maturity_date: int

class TreasuryOperationResultDTO(TypedDict):
    """Result of a treasury market operation."""
    success: bool
    bonds_exchanged: int
    cash_exchanged: float
    message: str

# ==============================================================================
# Interface
# ==============================================================================

class ITreasuryService(Protocol):
    """
    Interface for the Treasury Service, managing government debt issuance and
    interacting with the Central Bank for open market operations.
    """

    def execute_market_purchase(self, buyer_id: int | str, target_cash_amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> TreasuryOperationResultDTO:
        """
        Executes a purchase of bonds from the market (e.g. by Central Bank).
        The caller (buyer) provides cash, and receives bonds.
        """
        ...

    def execute_market_sale(self, seller_id: int | str, target_cash_amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> TreasuryOperationResultDTO:
        """
        Executes a sale of bonds to the market (e.g. by Central Bank).
        The caller (seller) provides bonds, and receives cash.
        """
        ...
