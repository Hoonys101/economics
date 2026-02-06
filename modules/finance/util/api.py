from typing import Any
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

def get_asset_balance(agent: Any, currency: CurrencyCode = DEFAULT_CURRENCY) -> float:
    """
    Safely retrieves an agent's financial asset balance, handling legacy data structures.
    This is the canonical way to check an agent's cash.
    """
    if hasattr(agent, 'wallet') and agent.wallet is not None:
        return agent.wallet.get_balance(currency)

    # Legacy fallbacks
    assets_raw = getattr(agent, 'assets', 0.0)
    if isinstance(assets_raw, dict):
        return assets_raw.get(currency, 0.0)
    try:
        return float(assets_raw) if currency == DEFAULT_CURRENCY else 0.0
    except (TypeError, ValueError):
        return 0.0
