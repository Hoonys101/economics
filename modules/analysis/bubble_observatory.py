from typing import List, Optional
import math
import statistics
import logging

from modules.market.housing_planner_api import IBubbleObservatory, HousingBubbleMetricsDTO
from simulation.engine import Simulation

logger = logging.getLogger(__name__)

class BubbleObservatory(IBubbleObservatory):
    """
    Monitors the housing market for signs of a bubble.
    Collects metrics on Price, Credit, and Leverage.
    """

    def __init__(self, simulation: Simulation):
        self.simulation = simulation
        self.last_m2 = 0.0

        # Initialize last_m2
        if hasattr(self.simulation.world_state, 'calculate_total_money'):
             self.last_m2 = self.simulation.world_state.calculate_total_money()

    def collect_metrics(self) -> HousingBubbleMetricsDTO:
        state = self.simulation.world_state
        tick = state.time

        # 1. House Price Index (Average Estimated Value)
        # We use estimated value of all units to gauge market level
        units = state.real_estate_units
        prices = [u.estimated_value for u in units if u.estimated_value > 0]
        avg_price = statistics.mean(prices) if prices else 0.0

        # 2. M2 Growth Rate
        current_m2 = state.calculate_total_money()
        if self.last_m2 == 0:
            growth_rate = 0.0
        else:
            growth_rate = (current_m2 - self.last_m2) / self.last_m2

        self.last_m2 = current_m2

        # 3. New Mortgage Volume & LTV/DTI from Transactions
        # We scan this tick's housing transactions
        # Transactions are in state.transactions (all of them? or just this tick?)
        # state.transactions accumulates. We need to filter by tick.
        # But state.transactions list grows indefinitely? (Memory leak risk, but addressed in other TD).
        # We filter by t.time == tick.

        housing_txs = [t for t in state.transactions if t.transaction_type == "housing" and t.time == tick]

        new_mortgage_vol = 0.0
        ltvs = []
        dtis = []

        bank = state.bank
        TICKS_PER_YEAR = getattr(self.simulation.config_module, 'TICKS_PER_YEAR', 100)

        for tx in housing_txs:
            price = tx.price
            if price <= 0: continue

            # Check for Mortgage
            if tx.metadata and "mortgage_id" in tx.metadata:
                mid = tx.metadata["mortgage_id"]
                loan = None

                # Resolve Loan Object
                # Try explicit string construction
                lid_str = f"loan_{mid}"
                if lid_str in bank.loans:
                    loan = bank.loans[lid_str]
                else:
                    # Search
                    for k, l in bank.loans.items():
                        # Heuristic matching if ID formats differ
                         if str(mid) in k:
                             loan = l
                             break

                if loan:
                    new_mortgage_vol += loan.principal

                    # LTV
                    ltv = loan.principal / price
                    ltvs.append(ltv)

                    # DTI (Approximate)
                    buyer = self.simulation.agents.get(tx.buyer_id)
                    if buyer and hasattr(buyer, 'current_wage'):
                        annual_income = buyer.current_wage * TICKS_PER_YEAR
                        monthly_income = annual_income / 12.0

                        # Monthly Payment
                        # Use Loan Interest
                        r = loan.annual_interest_rate / 12.0
                        n = getattr(loan, 'term_ticks', 360) # Assuming term_ticks approx months or we convert?
                        # Bank stores term_ticks.
                        # If term_ticks is large (e.g. 3600), we need conversion.
                        # Usually term_ticks matches Simulation Ticks.
                        # But mortgage calc usually based on Months.
                        # Let's use standard approximation for metric: 360 months.
                        months = 360

                        if r == 0:
                            payment = loan.principal / months
                        else:
                            payment = loan.principal * (r * (1+r)**months) / ((1+r)**months - 1)

                        # Existing Debt?
                        # Hard to get exact existing debt payment snapshot at moment of tx.
                        # We just use this loan's DTI contribution (Front-End DTI).
                        if monthly_income > 0:
                            dti = payment / monthly_income
                            dtis.append(dti)

        avg_ltv = statistics.mean(ltvs) if ltvs else 0.0
        avg_dti = statistics.mean(dtis) if dtis else 0.0

        # 4. Price-to-Income Ratio (PIR)
        TICKS_PER_YEAR = getattr(self.simulation.config_module, 'TICKS_PER_YEAR', 100)
        all_agents = self.simulation.agents.values()
        household_incomes = [
            agent.current_wage * TICKS_PER_YEAR
            for agent in all_agents
            if hasattr(agent, 'current_wage') and agent.current_wage > 0
        ]

        avg_annual_income = statistics.mean(household_incomes) if household_incomes else 0.0
        pir = (avg_price / avg_annual_income) if avg_annual_income > 0 else 0.0

        # PIR Alarm
        if pir > 20.0:
            logger.warning(f"High PIR detected: {pir:.2f}. Avg House Price: {avg_price:.2f}, Avg Annual Income: {avg_annual_income:.2f}")

        metrics: HousingBubbleMetricsDTO = {
            "tick": tick,
            "house_price_index": avg_price,
            "m2_growth_rate": growth_rate,
            "new_mortgage_volume": new_mortgage_vol,
            "average_ltv": avg_ltv,
            "average_dti": avg_dti,
            "pir": pir
        }

        # Log to file (append)
        # "logs/housing_bubble_monitor.csv"
        # We should use a CSV writer or logger.
        # Minimal implementation:
        try:
            import os
            os.makedirs("logs", exist_ok=True)
            file_exists = os.path.isfile("logs/housing_bubble_monitor.csv")

            with open("logs/housing_bubble_monitor.csv", "a") as f:
                if not file_exists:
                    f.write("tick,house_price_index,m2_growth_rate,new_mortgage_volume,average_ltv,average_dti,pir\n")

                f.write(f"{tick},{avg_price:.2f},{growth_rate:.6f},{new_mortgage_vol:.2f},{avg_ltv:.4f},{avg_dti:.4f},{pir:.2f}\n")
        except Exception as e:
            logger.error(f"BubbleObservatory: Failed to log metrics. {e}")

        return metrics
