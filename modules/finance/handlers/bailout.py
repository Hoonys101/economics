from typing import Any, Dict
import logging
import uuid
from modules.finance.api import ITransactionHandler
from modules.system.api import AssetBuyoutRequestDTO, IAssetRecoverySystem, AssetBuyoutResultDTO

logger = logging.getLogger(__name__)

class BailoutHandler(ITransactionHandler):
    """
    Handler for Bailout Transactions (Asset Buyouts).
    Delegates execution to the Asset Recovery System (Public Manager).
    """
    def __init__(self, asset_recovery_system: IAssetRecoverySystem):
        self.asset_recovery_system = asset_recovery_system
        self._results: Dict[str, AssetBuyoutResultDTO] = {}

    def validate(self, request: Any, context: Any) -> bool:
        """
        Validates the bailout request.
        """
        if not isinstance(request, AssetBuyoutRequestDTO):
            return False

        # Additional validation (e.g. check if seller exists) could be added here
        # But we rely on AssetRecoverySystem to handle business logic validation usually.
        # This layer validates DTO integrity.
        return True

    def execute(self, request: Any, context: Any) -> AssetBuyoutResultDTO:
        """
        Executes the asset buyout.
        """
        if not isinstance(request, AssetBuyoutRequestDTO):
             raise ValueError("Invalid request type for BailoutHandler")

        result = self.asset_recovery_system.execute_asset_buyout(request)
        if result.success:
            tx_id = result.transaction_id or str(uuid.uuid4())
            self._results[tx_id] = result
        return result

    def rollback(self, transaction_id: str, context: Any) -> bool:
        """
        Rollback for bailouts delegates to Asset Recovery System.
        """
        result = self._results.get(transaction_id)
        if not result:
            logger.warning(f"Rollback requested for unknown bailout transaction: {transaction_id}")
            return False

        try:
            success = self.asset_recovery_system.rollback_asset_buyout(result)
            if success:
                del self._results[transaction_id]
                logger.info(f"Successfully rolled back bailout transaction {transaction_id}.")
            else:
                logger.error(f"Failed to rollback bailout transaction {transaction_id}.")
            return success
        except Exception as e:
            logger.critical(f"CRITICAL: Rollback exception for Bailout {transaction_id}. Error: {e}")
            return False
