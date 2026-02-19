import logging
import random
from typing import List, Any, Optional, TYPE_CHECKING, Dict
from simulation.models import Transaction
from modules.system.api import DEFAULT_CURRENCY

if TYPE_CHECKING:
    from simulation.models import Transaction

logger = logging.getLogger(__name__)

class MinistryOfEducation:
    def __init__(self, config_module: Any):
        self.config_module = config_module

    def run_public_education(self, households: List[Any], government: Any, current_tick: int) -> List[Transaction]:
        """
        WO-054: Public Education System Implementation.
        Returns a list of Transactions.
        """
        transactions = []
        budget_ratio = getattr(self.config_module, "PUBLIC_EDU_BUDGET_RATIO", 0.20)
        # WO-057 Deficit Spending: Budget is based on REVENUE, not ASSETS

        # Handle revenue_this_tick being Dict or float
        revenue = 0.0
        if isinstance(government.revenue_this_tick, dict):
            revenue = government.revenue_this_tick.get(DEFAULT_CURRENCY, 0.0)
        else:
            try:
                revenue = float(government.revenue_this_tick)
            except (ValueError, TypeError):
                revenue = 0.0

        edu_budget = revenue * budget_ratio
        
        active_households = [h for h in households if h._bio_state.is_active]
        if not active_households:
            return []

        # Identify Potential Teachers (Households with Education > 0)
        teachers = [h for h in active_households if h._econ_state.education_level > 0]
        # Fallback if no educated households (Generation 0)
        if not teachers:
            teachers = active_households

        active_households.sort(key=lambda x: x._econ_state.wallet.get_balance(DEFAULT_CURRENCY))
        cutoff_idx = int(len(active_households) * getattr(self.config_module, "SCHOLARSHIP_WEALTH_PERCENTILE", 0.20))
        poor_households = set(h.id for h in active_households[:cutoff_idx])

        costs = getattr(self.config_module, "EDUCATION_COST_PER_LEVEL", {1: 500})
        scholarship_potential_threshold = getattr(self.config_module, "SCHOLARSHIP_POTENTIAL_THRESHOLD", 0.7)

        for agent in active_households:
            current_level = agent._econ_state.education_level
            next_level = current_level + 1
            cost = costs.get(next_level, 100000.0)

            # Select Teacher for this student
            teacher = random.choice(teachers)

            if current_level == 0:
                if edu_budget >= cost:
                    # Sync Financing check in Processor (handled by Bond txs if assets low)
                    # For Education, we just generate the tx.
                    tx = Transaction(
                        buyer_id=government.id,
                        seller_id=teacher.id,
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
                    , total_pennies=int(cost * 1.0 * 100))
                    transactions.append(tx)
                    edu_budget -= cost
                    logger.debug(f"EDU_BASIC_GRANT_PENDING | Household {agent.id} nominated for Level 1.")

            elif current_level >= 1:
                is_poor = agent.id in poor_households
                has_potential = agent._econ_state.aptitude >= scholarship_potential_threshold

                if is_poor and has_potential:
                    subsidy = cost * 0.8
                    student_share = cost * 0.2

                    if edu_budget >= subsidy and agent._econ_state.wallet.get_balance(DEFAULT_CURRENCY) >= student_share:
                        # 1. Government Subsidy Tx (Gov -> Teacher)
                        tx_subsidy = Transaction(
                            buyer_id=government.id,
                            seller_id=teacher.id,
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
                        , total_pennies=int(subsidy * 1.0 * 100))
                        # 2. Student Share Tx (Student -> Teacher)
                        tx_student = Transaction(
                            buyer_id=agent.id,
                            seller_id=teacher.id,
                            item_id=f"education_level_{next_level}_tuition",
                            quantity=1.0,
                            price=student_share,
                            market_id="system",
                            transaction_type="education_spending",
                            time=current_tick
                        , total_pennies=int(student_share * 1.0 * 100))
                        transactions.append(tx_subsidy)
                        transactions.append(tx_student)
                        edu_budget -= subsidy
                        logger.info(f"EDU_SCHOLARSHIP_PENDING | Household {agent.id} nominated for Level {next_level}.")

        return transactions
