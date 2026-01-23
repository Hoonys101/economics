import logging
from typing import List, Any

logger = logging.getLogger(__name__)


class MinistryOfEducation:
    def __init__(self, config_module: Any):
        self.config_module = config_module

    def run_public_education(
        self,
        households: List[Any],
        government: Any,
        current_tick: int,
        reflux_system: Any = None,
    ) -> None:
        """
        WO-054: Public Education System Implementation.
        1. Free Basic Education (Level 0 -> 1)
        2. Meritocratic Scholarship (Top Talent + Low Wealth)
        """
        budget_ratio = getattr(self.config_module, "PUBLIC_EDU_BUDGET_RATIO", 0.20)
        # WO-057 Deficit Spending: Budget is based on REVENUE, not ASSETS
        edu_budget = government.revenue_this_tick * budget_ratio
        spent_total = 0.0

        active_households = [h for h in households if getattr(h, "is_active", False)]
        if not active_households:
            return

        active_households.sort(key=lambda x: x.assets)
        cutoff_idx = int(
            len(active_households)
            * getattr(self.config_module, "SCHOLARSHIP_WEALTH_PERCENTILE", 0.20)
        )
        poor_households = set(h.id for h in active_households[:cutoff_idx])

        costs = getattr(self.config_module, "EDUCATION_COST_PER_LEVEL", {1: 500})
        scholarship_potential_threshold = getattr(
            self.config_module, "SCHOLARSHIP_POTENTIAL_THRESHOLD", 0.7
        )

        for agent in active_households:
            current_level = getattr(agent, "education_level", 0)
            next_level = current_level + 1
            cost = costs.get(next_level, 100000.0)

            if current_level == 0:
                if edu_budget >= cost:
                    agent.education_level = 1
                    edu_budget -= cost
                    government._sub_assets(cost)
                    spent_total += cost

                    logger.debug(
                        f"EDU_BASIC_GRANT | Household {agent.id} promoted to Level 1. Cost: {cost}",
                        extra={
                            "tick": current_tick,
                            "agent_id": government.id,
                            "target_id": agent.id,
                        },
                    )

            elif current_level >= 1:
                is_poor = agent.id in poor_households
                has_potential = (
                    getattr(agent, "aptitude", 0.0) >= scholarship_potential_threshold
                )

                if is_poor and has_potential:
                    subsidy = cost * 0.8
                    student_share = cost * 0.2

                    if edu_budget >= subsidy and agent.assets >= student_share:
                        agent.education_level = next_level
                        edu_budget -= subsidy
                        government._sub_assets(subsidy)
                        spent_total += subsidy

                        agent._sub_assets(student_share)
                        if reflux_system:
                            reflux_system.capture(
                                student_share,
                                f"Household_{agent.id}",
                                "education_tuition",
                            )

                        logger.info(
                            f"EDU_SCHOLARSHIP | Household {agent.id} (Aptitude {agent.aptitude:.2f}) promoted to Level {next_level}. Subsidy: {subsidy:.2f}, Student Share: {student_share:.2f}",
                            extra={
                                "tick": current_tick,
                                "agent_id": government.id,
                                "target_id": agent.id,
                                "aptitude": agent.aptitude,
                            },
                        )

        government.expenditure_this_tick += spent_total
        government.total_money_issued += spent_total
        if reflux_system:
            reflux_system.capture(spent_total, str(government.id), "education_services")

        government.current_tick_stats["education_spending"] = spent_total
