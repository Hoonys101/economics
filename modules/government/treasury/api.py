# --- modules/government/treasury/api.py ---
from __future__ import annotations
from typing import Protocol, TypedDict, Literal, List, Union
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
    face_value: int # MIGRATION: pennies
    yield_rate: float
    maturity_date: int

class TreasuryOperationResultDTO(TypedDict):
    """Result of a treasury market operation."""
    success: bool
    bonds_exchanged: int
    cash_exchanged: int # MIGRATION: pennies
    message: str

# ==============================================================================
# Interface
# ==============================================================================

class ITreasuryService(Protocol):
    """
    Interface for the Treasury Service, managing government debt issuance and
    interacting with the Central Bank for open market operations.
    """

    def execute_market_purchase(self, buyer_id: Union[int, str], target_cash_amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> TreasuryOperationResultDTO:
        """
        Executes a purchase of bonds from the market (e.g. by Central Bank).
        The caller (buyer) provides cash, and receives bonds.
        target_cash_amount: int pennies
        """
        ...

    def execute_market_sale(self, seller_id: Union[int, str], target_cash_amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> TreasuryOperationResultDTO:
        """
        Executes a sale of bonds to the market (e.g. by Central Bank).
        The caller (seller) provides bonds, and receives cash.
        target_cash_amount: int pennies
        """
        ...
