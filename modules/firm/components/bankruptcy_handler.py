from __future__ import annotations
from typing import Any
import logging

from modules.firm.api import IBankruptcyHandler

logger = logging.getLogger(__name__)

class BankruptcyHandler(IBankruptcyHandler):
    """
    Component for handling firm liquidation and graceful exit.
    """

    def trigger_liquidation(self, firm: Any, reason: str) -> None:
        """
        Initiates the liquidation process for a zombie/insolvent firm.
        """
        # 1. Log the event
        logger.warning(
            f"LIQUIDATION_TRIGGERED | Firm {firm.id} is insolvent. Reason: {reason}",
            extra={"agent_id": firm.id, "reason": reason}
        )

        # 2. Execute Asset Liquidation (returns recovered cash)
        # Note: firm.liquidate_assets usually takes current_tick.
        # However, `firm` is Any here. Assuming it has the method.
        # We need current_tick. Where do we get it?
        # The protocol doesn't pass tick.
        # But Firm usually has `current_tick` if passed during execution context?
        # Or we can pass -1 if unknown, or fix the protocol to include tick?
        # The Spec for `generate_transactions` (where this is called) has `current_time`.
        # I should probably update the protocol if I can, but I just finalized `modules/firm/api.py`.
        # I can update `Firm` to store `last_tick` or pass it via `firm.age`?
        # Or just pass -1. `Firm.liquidate_assets` defaults to -1.

        try:
            recovered_assets = firm.liquidate_assets()
        except Exception as e:
            logger.error(f"LIQUIDATION_ERROR | Failed to liquidate assets for Firm {firm.id}: {e}")
            recovered_assets = {}

        # 3. Deactivate Firm
        firm.is_active = False
        firm.is_bankrupt = True # Redundant if liquidate_assets sets it, but safe.

        # 4. Log Outcome
        logger.info(
            f"LIQUIDATION_COMPLETE | Firm {firm.id} liquidated. Recovered: {recovered_assets}",
            extra={"agent_id": firm.id, "recovered_assets": recovered_assets}
        )
