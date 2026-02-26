import logging
from typing import Any
from modules.finance.api import ITransactionHandler
from modules.system.api import AssetBuyoutRequestDTO, IAssetRecoverySystem, AssetBuyoutResultDTO

class BailoutHandler(ITransactionHandler):
    """
    Handler for Bailout Transactions (Asset Buyouts).
    Delegates execution to the Asset Recovery System (Public Manager).
    """
    def __init__(self, asset_recovery_system: IAssetRecoverySystem):
        self.asset_recovery_system = asset_recovery_system
        self.logger = logging.getLogger(__name__)

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

        return self.asset_recovery_system.execute_asset_buyout(request)

    def rollback(self, transaction_id: str, context: Any) -> bool:
        """
        Rollback for bailouts reverses the asset buyout in the recovery system.
        Expects AssetBuyoutRequestDTO in the context.
        """
        if not isinstance(context, AssetBuyoutRequestDTO):
            self.logger.error(f"Rollback failed for transaction {transaction_id}. Invalid context type: {type(context)}. Expected AssetBuyoutRequestDTO.")
            return False

        return self.asset_recovery_system.rollback_asset_buyout(context)
