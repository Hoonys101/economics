from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from simulation.engine import Simulation
from simulation.dtos.watchtower import (
    DashboardSnapshotDTO, SystemIntegrityDTO, MacroEconomyDTO, MonetaryDTO, PoliticsDTO
)
from modules.system.api import DEFAULT_CURRENCY

logger = logging.getLogger(__name__)

class DashboardService:
    def __init__(self, simulation: Simulation):
        self.simulation = simulation
        self._last_tick_time = datetime.now()
        self._last_tick = 0

    def get_snapshot(self) -> DashboardSnapshotDTO:
        state = self.simulation.world_state
        tracker = state.tracker

        # 1. System Integrity
        m2_leak = self._calculate_m2_leak(state)

        # FPS Calculation
        current_time = datetime.now()
        delta_seconds = (current_time - self._last_tick_time).total_seconds()
        fps = 0.0
        if delta_seconds > 0:
            tick_diff = state.time - self._last_tick
            if tick_diff > 0:
                fps = tick_diff / delta_seconds
                # Only update baseline if we actually advanced (simple smoothing)
                self._last_tick_time = current_time
                self._last_tick = state.time

        # 2. Macro Economy
        latest_metrics = {}
        if tracker:
            latest_metrics = tracker.get_latest_indicators()

        gdp_growth = 0.0
        # Calculate from government GDP history if available
        gov = state.governments[0] if state.governments else None

        if gov and hasattr(gov, 'gdp_history') and len(gov.gdp_history) >= 2:
            current = gov.gdp_history[-1]
            prev = gov.gdp_history[-2]
            if prev > 0:
                gdp_growth = ((current - prev) / prev) * 100.0

        inflation_rate = 0.0
        if gov and gov.sensory_data:
             inflation_rate = gov.sensory_data.inflation_sma * 100.0
        elif tracker:
             # Fallback to CPI change if sensory data not available
             cpi_list = tracker.metrics.get("goods_price_index", [])
             if len(cpi_list) >= 2 and cpi_list[-2] > 0:
                 inflation_rate = ((cpi_list[-1] - cpi_list[-2]) / cpi_list[-2]) * 100.0

        unemployment_rate = latest_metrics.get("unemployment_rate", 0.0)

        gini_coefficient = 0.0
        if gov and gov.sensory_data:
            gini_coefficient = gov.sensory_data.gini_index

        # 3. Monetary
        base_rate = 0.0
        if state.central_bank:
            base_rate = getattr(state.central_bank, "base_rate", 0.0) * 100.0

        interbank_rate = 0.0
        # Call Market is usually 'loan_market' in simple setup or managed by CallMarketService
        loan_market = state.markets.get("loan_market")
        if loan_market:
             interbank_rate = getattr(loan_market, "interest_rate", 0.0) * 100.0

        m2_supply = 0.0
        if tracker:
            m2_supply = tracker.get_m2_money_supply(state)

        exchange_rates = {}
        if tracker and hasattr(tracker, 'exchange_engine'):
            exchange_rates = tracker.exchange_engine.get_all_rates()

        # 4. Politics
        party = "NEUTRAL"
        approval_rating = 0.0
        social_cohesion = 0.5

        if gov:
            party = gov.ruling_party.name if hasattr(gov.ruling_party, 'name') else str(gov.ruling_party)
            approval_rating = gov.approval_rating
            # Social cohesion - placeholder
            social_cohesion = gov.approval_rating # Proxy for now

        current_events = []

        return DashboardSnapshotDTO(
            tick=state.time,
            timestamp=datetime.now().isoformat(),
            system_integrity=SystemIntegrityDTO(m2_leak=m2_leak, fps=fps),
            macro_economy=MacroEconomyDTO(
                gdp_growth=gdp_growth,
                inflation_rate=inflation_rate,
                unemployment_rate=unemployment_rate,
                gini_coefficient=gini_coefficient
            ),
            monetary=MonetaryDTO(
                base_rate=base_rate,
                interbank_rate=interbank_rate,
                m2_supply=m2_supply,
                exchange_rates=exchange_rates
            ),
            politics=PoliticsDTO(
                party=party,
                approval_rating=approval_rating,
                social_cohesion=social_cohesion,
                current_events=current_events
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
