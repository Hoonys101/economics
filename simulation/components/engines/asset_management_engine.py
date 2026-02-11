from __future__ import annotations
import logging
from modules.firm.api import IAssetManagementEngine, AssetManagementInputDTO, AssetManagementResultDTO

logger = logging.getLogger(__name__)

class AssetManagementEngine(IAssetManagementEngine):
    """
    Stateless engine for handling investments in capital and automation.
    Implements IAssetManagementEngine.
    """

    def invest(self, input_dto: AssetManagementInputDTO) -> AssetManagementResultDTO:
        """
        Calculates the outcome of an investment in CAPEX or Automation.
        Returns a DTO describing the resulting state changes.
        """
        config = input_dto.firm_snapshot.config
        state = input_dto.firm_snapshot.production

        # Guard clause for negative investment
        if input_dto.investment_amount <= 0:
             return AssetManagementResultDTO(
                success=False,
                message="Investment amount must be positive."
            )

        try:
            if input_dto.investment_type == "AUTOMATION":
                cost_per_pct = config.automation_cost_per_pct
                if cost_per_pct <= 0:
                     return AssetManagementResultDTO(success=False, message="Invalid automation cost configuration.")

                gained_automation = (input_dto.investment_amount / cost_per_pct) / 100.0

                # Check for max automation (1.0)
                current_automation = state.automation_level
                potential_automation = current_automation + gained_automation
                actual_gained = gained_automation

                if potential_automation > 1.0:
                    actual_gained = 1.0 - current_automation
                    # We could refund the excess, but for now we consume the full budget
                    # as implied by current implementation (simple sink).
                    # Or we should cap the cost?
                    # Current implementation: simple division.
                    # I will stick to simple division but cap the gain.

                return AssetManagementResultDTO(
                    success=True,
                    automation_level_increase=actual_gained,
                    actual_cost=input_dto.investment_amount
                )

            elif input_dto.investment_type == "CAPEX":
                capital_to_output_ratio = config.capital_to_output_ratio
                if capital_to_output_ratio <= 0:
                     return AssetManagementResultDTO(success=False, message="Invalid capital to output ratio.")

                efficiency = 1.0 / capital_to_output_ratio
                added_capital = input_dto.investment_amount * efficiency

                return AssetManagementResultDTO(
                    success=True,
                    capital_stock_increase=added_capital,
                    actual_cost=input_dto.investment_amount
                )

            else:
                return AssetManagementResultDTO(
                    success=False,
                    message=f"Unknown investment type: {input_dto.investment_type}"
                )

        except Exception as e:
            logger.error(f"ASSET_MGMT_ERROR | Firm {input_dto.firm_snapshot.id}: {e}")
            return AssetManagementResultDTO(
                success=False,
                message=str(e)
            )
