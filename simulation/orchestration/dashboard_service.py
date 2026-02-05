from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from simulation.engine import Simulation
from simulation.dtos.watchtower import (
    WatchtowerSnapshotDTO, IntegrityDTO, MacroDTO, FinanceDTO,
    FinanceRatesDTO, FinanceSupplyDTO, PoliticsDTO, PoliticsApprovalDTO,
    PoliticsStatusDTO, PoliticsFiscalDTO, PopulationDTO,
    PopulationDistributionDTO, PopulationMetricsDTO
)
from modules.system.api import DEFAULT_CURRENCY

logger = logging.getLogger(__name__)

class DashboardService:
    def __init__(self, simulation: Simulation):
        self.simulation = simulation
        self._last_tick_time = datetime.now()
        self._last_tick = 0

    def get_snapshot(self) -> WatchtowerSnapshotDTO:
        state = self.simulation.world_state
        tracker = state.tracker
        gov = state.governments[0] if state.governments else None

        # --- 1. System Integrity ---
        m2_leak = self._calculate_m2_leak(state)

        # FPS Calculation
        current_time = datetime.now()
        delta_seconds = (current_time - self._last_tick_time).total_seconds()
        fps = 0.0
        if delta_seconds > 0:
            tick_diff = state.time - self._last_tick
            if tick_diff > 0:
                fps = tick_diff / delta_seconds
                self._last_tick_time = current_time
                self._last_tick = state.time

        # --- 2. Macro Economy ---
        latest = tracker.get_latest_indicators() if tracker else {}

        # GDP (Nominal)
        gdp = latest.get("gdp", 0.0)

        # CPI (Goods Price Index)
        cpi = latest.get("goods_price_index", 1.0)

        # Unemployment
        unemploy = latest.get("unemployment_rate", 0.0)

        # Gini
        gini = latest.get("gini", 0.0)

        # --- 3. Finance ---
        # Rates
        base_rate = 0.0
        if state.central_bank:
            base_rate = getattr(state.central_bank, "base_rate", 0.0) * 100.0

        loan_rate = 0.0
        loan_market = state.markets.get("loan_market")
        if loan_market:
             loan_rate = getattr(loan_market, "interest_rate", 0.0) * 100.0

        call_rate = base_rate # Proxy if no call market
        if state.markets.get("call_market"):
             # Assuming call market has interest_rate
             call_rate = getattr(state.markets["call_market"], "interest_rate", 0.0) * 100.0

        savings_rate = max(0.0, loan_rate - 2.0) # Heuristic: Spread

        # Supply
        m2 = tracker.get_m2_money_supply(state) if tracker else 0.0
        velocity = latest.get("velocity_of_money", 0.0)
        m0 = m2 * 0.2 # Placeholder/Heuristic
        m1 = m2 * 0.8 # Placeholder/Heuristic

        # --- 4. Politics ---
        # Approval
        approval_total = gov.approval_rating if gov else 0.0
        # Breakdown placeholders (can be enhanced in Tracker later)
        approval_low = approval_total
        approval_mid = approval_total
        approval_high = approval_total

        # Status
        party = "NEUTRAL"
        if gov:
            party = gov.ruling_party.name if hasattr(gov.ruling_party, 'name') else str(gov.ruling_party)

        cohesion = latest.get("social_cohesion", 0.5)

        # Fiscal
        revenue = 0.0
        welfare = 0.0
        debt = 0.0
        if gov:
             # Assuming sensory_data or ledger has these
             # Revenue: last turn revenue?
             revenue = getattr(gov, "last_revenue", 0.0)
             # Welfare:
             # gov.welfare_manager?
             # For now, 0.0 if not easily accessible without side effects
             pass

        # --- 5. Population ---
        q1 = latest.get("quintile_1_avg_assets", 0.0)
        q2 = latest.get("quintile_2_avg_assets", 0.0)
        q3 = latest.get("quintile_3_avg_assets", 0.0)
        q4 = latest.get("quintile_4_avg_assets", 0.0)
        q5 = latest.get("quintile_5_avg_assets", 0.0)

        active_count = latest.get("active_population", 0)

        # Demographics (Restored from legacy SnapshotViewModel)
        birth_rate = 0.0
        death_rate = 0.0

        repo = getattr(state, "repository", None)
        if repo and active_count > 0:
            start_tick = max(0, state.time - 5)
            # Fetch attrition stats for death rate
            attrition = repo.agents.get_attrition_counts(start_tick, state.time, run_id=state.run_id)
            death_count = attrition.get("death_count", 0)
            death_rate = (death_count / active_count) * 100.0

            # TODO: Implement Birth Rate tracking in Repository or Tracker

        return WatchtowerSnapshotDTO(
            tick=state.time,
            status="RUNNING", # TODO: Hook into simulation status if available
            integrity=IntegrityDTO(m2_leak=m2_leak, fps=fps),
            macro=MacroDTO(
                gdp=gdp,
                cpi=cpi,
                unemploy=unemploy,
                gini=gini
            ),
            finance=FinanceDTO(
                rates=FinanceRatesDTO(base=base_rate, call=call_rate, loan=loan_rate, savings=savings_rate),
                supply=FinanceSupplyDTO(m0=m0, m1=m1, m2=m2, velocity=velocity)
            ),
            politics=PoliticsDTO(
                approval=PoliticsApprovalDTO(total=approval_total, low=approval_low, mid=approval_mid, high=approval_high),
                status=PoliticsStatusDTO(ruling_party=party, cohesion=cohesion),
                fiscal=PoliticsFiscalDTO(revenue=revenue, welfare=welfare, debt=debt)
            ),
            population=PopulationDTO(
                                active_count=active_count,
                                metrics=PopulationMetricsDTO(birth=birth_rate, death=death_rate)
                            )
                        )

    def _calculate_m2_leak(self, state) -> float:
        m2_current = state.calculate_total_money().get(DEFAULT_CURRENCY, 0.0)
        m2_start = state.baseline_money_supply

        delta_issued = 0.0
        delta_destroyed = 0.0

        gov = state.governments[0] if state.governments else None

        if gov and hasattr(gov, "monetary_ledger"):
            ledger = gov.monetary_ledger
            delta_issued = ledger.total_money_issued.get(DEFAULT_CURRENCY, 0.0)
            delta_destroyed = ledger.total_money_destroyed.get(DEFAULT_CURRENCY, 0.0)

        expected_m2 = m2_start + delta_issued - delta_destroyed
        return m2_current - expected_m2
