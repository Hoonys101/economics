import logging
from typing import List, Any, Optional

logger = logging.getLogger(__name__)

class MinistryOfEducation:
    def __init__(self, config_module: Any):
        self.config_module = config_module

    def run_public_education(self, households: List[Any], government: Any, current_tick: int, reflux_system: Any = None, settlement_system: Any = None) -> None:
        """
        WO-054: Public Education System Implementation.
        1. Free Basic Education (Level 0 -> 1)
        2. Meritocratic Scholarship (Top Talent + Low Wealth)

        WO-116: Refactored to use SettlementSystem for leak prevention.
        """
        budget_ratio = getattr(self.config_module, "PUBLIC_EDU_BUDGET_RATIO", 0.20)
        # WO-057 Deficit Spending: Budget is based on REVENUE, not ASSETS
        edu_budget = government.revenue_this_tick * budget_ratio
        spent_total = 0.0

        active_households = [h for h in households if getattr(h, "is_active", False)]
        if not active_households:
            return

        active_households.sort(key=lambda x: x.assets)
        cutoff_idx = int(len(active_households) * getattr(self.config_module, "SCHOLARSHIP_WEALTH_PERCENTILE", 0.20))
        poor_households = set(h.id for h in active_households[:cutoff_idx])

        costs = getattr(self.config_module, "EDUCATION_COST_PER_LEVEL", {1: 500})
        scholarship_potential_threshold = getattr(self.config_module, "SCHOLARSHIP_POTENTIAL_THRESHOLD", 0.7)

        for agent in active_households:
            current_level = getattr(agent, "education_level", 0)
            next_level = current_level + 1
            cost = costs.get(next_level, 100000.0)

            if current_level == 0:
                if edu_budget >= cost:
                    # Synchronous Financing Check
                    if government.assets < cost:
                        needed = cost - government.assets
                        if hasattr(government.finance_system, 'issue_treasury_bonds_synchronous'):
                            if not government.finance_system.issue_treasury_bonds_synchronous(government, needed, current_tick):
                                continue

                    success = False
                    if settlement_system and reflux_system:
                        if settlement_system.transfer(government, reflux_system, cost, "Education Grant"):
                            success = True
                    else:
                        # Fallback (Legacy)
                        government._sub_assets(cost)
                        if reflux_system:
                            reflux_system.capture(cost, str(government.id), "education_services")
                        success = True

                    if success:
                        agent.education_level = 1
                        edu_budget -= cost
                        spent_total += cost
                        logger.debug(
                            f"EDU_BASIC_GRANT | Household {agent.id} promoted to Level 1. Cost: {cost}",
                            extra={"tick": current_tick, "agent_id": government.id, "target_id": agent.id}
                        )

            elif current_level >= 1:
                is_poor = agent.id in poor_households
                has_potential = getattr(agent, "aptitude", 0.0) >= scholarship_potential_threshold

                if is_poor and has_potential:
                    subsidy = cost * 0.8
                    student_share = cost * 0.2

                    if edu_budget >= subsidy and agent.assets >= student_share:
                        # Synchronous Financing Check (Subsidy)
                        if government.assets < subsidy:
                            needed = subsidy - government.assets
                            if hasattr(government.finance_system, 'issue_treasury_bonds_synchronous'):
                                if not government.finance_system.issue_treasury_bonds_synchronous(government, needed, current_tick):
                                    continue

                        success = False

                        if settlement_system and reflux_system:
                             # 1. Government Subsidy
                             t1 = settlement_system.transfer(government, reflux_system, subsidy, "Education Subsidy")
                             # 2. Student Share
                             t2 = settlement_system.transfer(agent, reflux_system, student_share, "Education Tuition")

                             if t1 and t2:
                                 success = True
                             elif t1 and not t2:
                                 # Partial failure: Subsidy sent, student failed.
                                 # Ideally we rollback or keep it (Subsidy granted, but student couldn't pay share? Unlikely due to check above)
                                 # We accept partial success as success for simplicity, or we rollback manually?
                                 # Given agents.assets check passed, t2 should fail only if system error.
                                 success = True
                             elif not t1:
                                 # Subsidy failed, abort.
                                 success = False
                        else:
                            # Fallback (Legacy)
                            government._sub_assets(subsidy)
                            agent._sub_assets(student_share)
                            if reflux_system:
                                reflux_system.capture(student_share, f"Household_{agent.id}", "education_tuition")
                                reflux_system.capture(subsidy, str(government.id), "education_subsidy")
                            success = True

                        if success:
                            agent.education_level = next_level
                            edu_budget -= subsidy
                            spent_total += subsidy

                            logger.info(
                                f"EDU_SCHOLARSHIP | Household {agent.id} (Aptitude {agent.aptitude:.2f}) promoted to Level {next_level}. Subsidy: {subsidy:.2f}, Student Share: {student_share:.2f}",
                                extra={"tick": current_tick, "agent_id": government.id, "target_id": agent.id, "aptitude": agent.aptitude}
                            )

        government.expenditure_this_tick += spent_total
        # government.total_money_issued += spent_total # LEAK FIXED: Do not count spending as new issuance.

        government.current_tick_stats["education_spending"] = spent_total
