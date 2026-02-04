from typing import List, Optional, Any, TYPE_CHECKING
import math
import statistics
import logging
import os

from modules.market.housing_planner_api import IBubbleObservatory, HousingBubbleMetricsDTO

if TYPE_CHECKING:
    from simulation.engine import Simulation

logger = logging.getLogger(__name__)

class BubbleMetricsCalculator:
    """
    Pure logic component for calculating housing bubble metrics.
    Separated from BubbleObservatory for SRP (TD-204).
    """
    def __init__(self, simulation_state: Any, config_module: Any, last_m2: float, agents: Any = None):
        self.state = simulation_state
        self.config = config_module
        self.last_m2 = last_m2
        self.current_m2 = 0.0
        # Prefer injected agents, fallback to state.agents
        self.agents = agents if agents is not None else getattr(simulation_state, 'agents', {})

    def calculate(self) -> HousingBubbleMetricsDTO:
        state = self.state
        tick = state.time

        # 1. House Price Index (Average Estimated Value)
        units = state.real_estate_units
        prices = [u.estimated_value for u in units if u.estimated_value > 0]
        avg_price = statistics.mean(prices) if prices else 0.0

        # 2. M2 Growth Rate
        # Calculate current M2 here so we can use it for growth rate
        if hasattr(state, 'calculate_total_money'):
            self.current_m2 = state.calculate_total_money()
        else:
            self.current_m2 = 0.0 # Fallback

        if self.last_m2 == 0:
            growth_rate = 0.0
        else:
            growth_rate = (self.current_m2 - self.last_m2) / self.last_m2

        # 3. New Mortgage Volume & LTV/DTI from Transactions
        transactions = getattr(state, 'transactions', [])
        housing_txs = [t for t in transactions if t.transaction_type == "housing" and t.time == tick]

        new_mortgage_vol = 0.0
        ltvs = []
        dtis = []

        bank = state.bank
        TICKS_PER_YEAR = getattr(self.config, 'TICKS_PER_YEAR', 100)

        # Access agents safely
        agents = self.agents
        if hasattr(agents, 'get'):
            get_agent = agents.get
        else:
            get_agent = lambda aid: None

        for tx in housing_txs:
            price = tx.price
            if price <= 0: continue

            if tx.metadata and "mortgage_id" in tx.metadata:
                mid = tx.metadata["mortgage_id"]
                loan = None

                # Resolve Loan
                if hasattr(bank, 'loans'):
                    lid_str = f"loan_{mid}"
                    if lid_str in bank.loans:
                        loan = bank.loans[lid_str]
                    else:
                        for k, l in bank.loans.items():
                             if str(mid) in k:
                                 loan = l
                                 break

                if loan:
                    new_mortgage_vol += loan.principal

                    # LTV
                    ltv = loan.principal / price
                    ltvs.append(ltv)

                    # DTI
                    buyer = get_agent(tx.buyer_id)
                    if buyer and hasattr(buyer, 'current_wage'):
                        annual_income = buyer.current_wage * TICKS_PER_YEAR
                        monthly_income = annual_income / 12.0

                        r = loan.annual_interest_rate / 12.0
                        n = getattr(loan, 'term_ticks', 360)
                        # Approximation: 360 months standard
                        months = 360

                        if r == 0:
                            payment = loan.principal / months
                        else:
                            payment = loan.principal * (r * (1+r)**months) / ((1+r)**months - 1)

                        if monthly_income > 0:
                            dti = payment / monthly_income
                            dtis.append(dti)

        avg_ltv = statistics.mean(ltvs) if ltvs else 0.0
        avg_dti = statistics.mean(dtis) if dtis else 0.0

        # 4. Price-to-Income Ratio (PIR)
        # Iterate all agents to get average income
        all_agents_values = agents.values() if hasattr(agents, 'values') else []
        household_incomes = [
            agent.current_wage * TICKS_PER_YEAR
            for agent in all_agents_values
            if hasattr(agent, 'current_wage') and agent.current_wage > 0
        ]

        avg_annual_income = statistics.mean(household_incomes) if household_incomes else 0.0
        pir = (avg_price / avg_annual_income) if avg_annual_income > 0 else 0.0

        if pir > 20.0:
            logger.warning(f"High PIR detected: {pir:.2f}. Avg House Price: {avg_price:.2f}, Avg Annual Income: {avg_annual_income:.2f}")

        return {
            "tick": tick,
            "house_price_index": avg_price,
            "m2_growth_rate": growth_rate,
            "new_mortgage_volume": new_mortgage_vol,
            "average_ltv": avg_ltv,
            "average_dti": avg_dti,
            "pir": pir
        }

class BubbleObservatory(IBubbleObservatory):
    """
    Monitors the housing market for signs of a bubble.
    Delegates calculation to BubbleMetricsCalculator and handles logging.
    """

    def __init__(self, simulation: Any):
        self.simulation = simulation
        self.last_m2 = 0.0

        # Initialize last_m2
        if hasattr(self.simulation.world_state, 'calculate_total_money'):
             self.last_m2 = self.simulation.world_state.calculate_total_money()

    def collect_metrics(self) -> HousingBubbleMetricsDTO:
        # Determine agents source
        # Prioritize simulation.agents if available, else world_state.agents
        agents = getattr(self.simulation, 'agents', getattr(self.simulation.world_state, 'agents', {}))

        calculator = BubbleMetricsCalculator(
            self.simulation.world_state,
            self.simulation.config_module,
            self.last_m2,
            agents=agents
        )

        metrics = calculator.calculate()

        # Update internal state (M2)
        self.last_m2 = calculator.current_m2

        # Log Logic (Side Effect)
        self._log_metrics(metrics)

        return metrics

    def _log_metrics(self, metrics: HousingBubbleMetricsDTO):
        """Writes metrics to CSV log."""
        try:
            os.makedirs("logs", exist_ok=True)
            file_path = "logs/housing_bubble_monitor.csv"
            file_exists = os.path.isfile(file_path)

            with open(file_path, "a") as f:
                if not file_exists:
                    f.write("tick,house_price_index,m2_growth_rate,new_mortgage_volume,average_ltv,average_dti,pir\n")

                f.write(f"{metrics['tick']},{metrics['house_price_index']:.2f},{metrics['m2_growth_rate']:.6f},{metrics['new_mortgage_volume']:.2f},{metrics['average_ltv']:.4f},{metrics['average_dti']:.4f},{metrics['pir']:.2f}\n")
        except Exception as e:
            logger.error(f"BubbleObservatory: Failed to log metrics. {e}")
