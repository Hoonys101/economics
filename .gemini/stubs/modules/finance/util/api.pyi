from modules.system.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY
from typing import Any

def get_asset_balance(agent: Any, currency: CurrencyCode = ...) -> float:
    """
    Safely retrieves an agent's financial asset balance, handling legacy data structures.
    This is the canonical way to check an agent's cash.
    """
