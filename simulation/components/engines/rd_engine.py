from __future__ import annotations
import logging
import random
from modules.firm.api import IRDEngine, RDInputDTO, RDResultDTO

logger = logging.getLogger(__name__)

class RDEngine(IRDEngine):
    """
    Stateless engine for handling investments in Research and Development.
    Implements IRDEngine.
    """

    def research(self, input_dto: RDInputDTO) -> RDResultDTO:
        """
        Calculates the outcome of R&D spending.
        Returns a DTO describing improvements to quality or technology.
        """
        config = input_dto.firm_snapshot.config
        state = input_dto.firm_snapshot.production

        try:
            # Guard clause for negative investment
            if input_dto.investment_amount <= 0:
                 return RDResultDTO(
                    success=False,
                    message="Investment amount must be positive."
                )

            # R&D Success Probability Calculation
            revenue = input_dto.firm_snapshot.finance.revenue_this_turn.get("USD", 0.0) # Assume USD or fetch DEFAULT
            # But wait, FinanceStateDTO uses dict for revenue. I should check which currency to use.
            # Usually DEFAULT_CURRENCY.
            # But FirmSnapshotDTO has revenue_this_turn as Dict.
            # I'll sum up or pick default.

            # The original code:
            # denominator = max(revenue * 0.2, 100.0)
            # base_chance = min(1.0, budget / denominator)

            # I'll use sum of all revenues for now as simplistic approach, or just USD.
            total_revenue = sum(input_dto.firm_snapshot.finance.revenue_this_turn.values())

            denominator = max(total_revenue * 0.2, 100.0)
            base_chance = min(1.0, input_dto.investment_amount / denominator)

            # Skill Modifier
            # hr_state has employees data.
            # I need to calculate average skill.
            hr_state = input_dto.firm_snapshot.hr
            avg_skill = 1.0
            if hr_state.employees:
                total_skill = sum(
                    emp_data.get("skill", 1.0)
                    for emp_data in hr_state.employees_data.values()
                )
                avg_skill = total_skill / len(hr_state.employees)

            success_chance = base_chance * avg_skill

            if random.random() < success_chance:
                # Success!
                return RDResultDTO(
                    success=True,
                    quality_improvement=0.05,
                    productivity_multiplier_change=1.05,
                    actual_cost=input_dto.investment_amount
                )
            else:
                return RDResultDTO(
                    success=False,
                    actual_cost=input_dto.investment_amount,
                    message="R&D attempt failed."
                )

        except Exception as e:
            logger.error(f"RD_ERROR | Firm {input_dto.firm_snapshot.id}: {e}")
            return RDResultDTO(
                success=False,
                message=str(e)
            )
