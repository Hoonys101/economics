from __future__ import annotations
from typing import TYPE_CHECKING
import math

from simulation.dtos import LaborResult

if TYPE_CHECKING:
    from simulation.core_agents import Household


class LaborManager:
    """
    Manages all labor-related activities for a Household.

    This component handles job searching, working, skill updates, and income
    tracking, separating these concerns from the core Household agent logic.
    """

    def __init__(self, household: "Household", config_module: any) -> None:
        """
        Initializes the LaborManager.

        Args:
            household: The household agent that owns this manager.
            config_module: The simulation's configuration module.
        """
        self._household = household
        self._config = config_module

    def work(self, hours: float) -> LaborResult:
        """
        Executes work for a given number of hours, earning income.

        Args:
            hours: The number of hours to work.

        Returns:
            A LaborResult DTO containing the hours worked and income earned.
        """
        if not self._household.is_employed or self._household.employer_id is None:
            return LaborResult(hours_worked=0, income_earned=0)

        income = self._household.current_wage * hours
        self._household.adjust_assets(income)
        self._household.add_labor_income(income)
        return LaborResult(hours_worked=hours, income_earned=income)

    def search_job(self) -> None:
        """
        Handles the logic for searching for a job.
        This method would be called by the household's decision-making process.
        """
        # This is a placeholder for more complex job searching logic.
        # The actual job searching is handled by the decision engine creating SELL orders for labor.
        pass

    def update_skills(self) -> None:
        """
        Updates the household's labor skill based on education experience.
        """
        # XP -> Skill Conversion Formula: Labor Skill = 1.0 + ln(XP + 1) * Talent
        log_growth = math.log1p(self._household.education_xp)  # ln(x+1)
        talent_factor = self._household.talent.base_learning_rate
        new_skill = 1.0 + (log_growth * talent_factor)

        old_skill = self._household.labor_skill
        self._household.labor_skill = new_skill

        if new_skill > old_skill + 0.1:
            self._household.logger.debug(
                f"SKILL_UP | Household {self._household.id} skill improved: {old_skill:.2f} -> {new_skill:.2f} (XP: {self._household.education_xp:.1f})",
                extra={"tags": ["education", "productivity"]},
            )

    def get_income(self) -> float:
        """
        Gets the total income earned in the current tick.

        Returns:
            The total income (labor + capital) for the current tick.
        """
        return self._household.labor_income_this_tick + self._household.capital_income_this_tick
