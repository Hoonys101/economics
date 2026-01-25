import logging
from typing import List, Any, Optional, TYPE_CHECKING
from simulation.models import Transaction

if TYPE_CHECKING:
    from simulation.models import Transaction

logger = logging.getLogger(__name__)

class MinistryOfEducation:
    def __init__(self, config_module: Any):
        self.config_module = config_module

    def run_public_education(self, households: List[Any], government: Any, current_tick: int, reflux_system: Any = None, settlement_system: Any = None) -> List[Transaction]:
        """
        WO-054: Public Education System Implementation.
        Returns a list of Transactions.
        """
        transactions = []
        budget_ratio = getattr(self.config_module, "PUBLIC_EDU_BUDGET_RATIO", 0.20)
        # WO-057 Deficit Spending: Budget is based on REVENUE, not ASSETS
        edu_budget = government.revenue_this_tick * budget_ratio
        
        active_households = [h for h in households if getattr(h, "is_active", False)]
        if not active_households:
            return []

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
                    # Sync Financing check in Processor (handled by Bond txs if assets low)
                    # For Education, we just generate the tx.
                    tx = Transaction(
                        buyer_id=government.id,
                        seller_id=reflux_system.id if reflux_system else 999999,
                        item_id="education_level_1",
                        quantity=1.0,
                        price=cost,
                        market_id="system",
                        transaction_type="education_spending",
                        time=current_tick,
                        metadata={
                            "triggers_effect": "EDUCATION_UPGRADE",
                            "target_agent_id": agent.id
                        }
                    )
                    transactions.append(tx)
                    edu_budget -= cost
                    logger.debug(f"EDU_BASIC_GRANT_PENDING | Household {agent.id} nominated for Level 1.")

            elif current_level >= 1:
                is_poor = agent.id in poor_households
                has_potential = getattr(agent, "aptitude", 0.0) >= scholarship_potential_threshold

                if is_poor and has_potential:
                    subsidy = cost * 0.8
                    student_share = cost * 0.2

                    if edu_budget >= subsidy and agent.assets >= student_share:
                        # 1. Government Subsidy Tx
                        tx_subsidy = Transaction(
                            buyer_id=government.id,
                            seller_id=reflux_system.id if reflux_system else 999999,
                            item_id=f"education_level_{next_level}_subsidy",
                            quantity=1.0,
                            price=subsidy,
                            market_id="system",
                            transaction_type="education_spending",
                            time=current_tick,
                            metadata={
                                "triggers_effect": "EDUCATION_UPGRADE",
                                "target_agent_id": agent.id
                            }
                        )
                        # 2. Student Share Tx
                        tx_student = Transaction(
                            buyer_id=agent.id,
                            seller_id=reflux_system.id if reflux_system else 999999,
                            item_id=f"education_level_{next_level}_tuition",
                            quantity=1.0,
                            price=student_share,
                            market_id="system",
                            transaction_type="education_spending",
                            time=current_tick
                        )
                        transactions.append(tx_subsidy)
                        transactions.append(tx_student)
                        edu_budget -= subsidy
                        logger.info(f"EDU_SCHOLARSHIP_PENDING | Household {agent.id} nominated for Level {next_level}.")

        return transactions
