from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState
from modules.system.api import DEFAULT_CURRENCY

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase0_PreTickMetrics(IPhaseStrategy):
    """
    Handles pre-tick metrics and baseline establishment.
    Extracted from TickOrchestrator.
    """
    def __init__(self, world_state: 'WorldState'):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        # Money Supply Verification (Tick 0/1)
        # Note: Time is incremented to 1 before this phase runs in TickOrchestrator
        if state.time == 1:
            if state.monetary_ledger:
                 baseline = state.monetary_ledger.get_total_m2_pennies(DEFAULT_CURRENCY)
                 self.world_state.baseline_money_supply = baseline
                 # Sync expected to actual at Genesis if not set
                 if state.monetary_ledger.get_expected_m2_pennies(DEFAULT_CURRENCY) == 0 and baseline > 0:
                     state.monetary_ledger.set_expected_m2(baseline, DEFAULT_CURRENCY)
            else:
                 money_dto = self.world_state.calculate_total_money()
                 self.world_state.baseline_money_supply = int(money_dto.total_m2_pennies)

            logger.info(
                f"MONEY_SUPPLY_BASELINE | Baseline Money Supply set to: {self.world_state.baseline_money_supply}",
                extra={"tick": state.time, "money_supply": self.world_state.baseline_money_supply}
            )

        # WO-IMPL-INDEX-BREAKER: Centralized Market Health Check
        if state.stock_market and getattr(self.world_state, 'index_circuit_breaker', None):
            circuit_breaker = self.world_state.index_circuit_breaker
            total_price_index = 0.0
            known_firms = set(state.stock_market.reference_prices.keys()) | set(state.stock_market.last_prices.keys())
            for firm_id in known_firms:
                price = state.stock_market.last_prices.get(firm_id, state.stock_market.reference_prices.get(firm_id, 0.0))
                total_price_index += price

            if state.time == 1 and total_price_index > 0:
                circuit_breaker.set_reference_index(total_price_index)

            circuit_breaker.check_market_health({'market_index': total_price_index}, state.time)

        return state

class Phase6_PostTickMetrics(IPhaseStrategy):
    """
    Handles post-tick metrics and verification.
    Extracted from TickOrchestrator.
    """
    def __init__(self, world_state: 'WorldState'):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        # Money Supply Verification (Post-Tick) & M2 Leak Calculation
        m2_leak_delta = 0.0
        if state.time >= 1:
            current_money = 0
            expected_money = 0

            if state.monetary_ledger:
                current_money = state.monetary_ledger.get_total_m2_pennies(DEFAULT_CURRENCY)
                expected_money = state.monetary_ledger.get_expected_m2_pennies(DEFAULT_CURRENCY)
                # Ensure baseline is synced to expected M2 (SSoT)
                self.world_state.baseline_money_supply = expected_money
            else:
                supply_dto = self.world_state.calculate_total_money()
                current_money = int(supply_dto.total_m2_pennies)
                expected_money = int(self.world_state.baseline_money_supply)

            m2_leak_delta = current_money - expected_money

            msg = f"MONEY_SUPPLY_CHECK | Current: {current_money}, Expected: {expected_money}, Delta: {m2_leak_delta}"
            extra_data = {"tick": state.time, "current": current_money, "expected": expected_money, "delta": m2_leak_delta, "tags": ["money_supply"]}

            tolerance = int(max(1000, expected_money * 0.001))
            if abs(m2_leak_delta) > tolerance:
                 logger.warning(msg, extra=extra_data)
            else:
                 logger.info(msg, extra=extra_data)

            # --- SSoT M2 Audit ---
            if state.settlement_system:
                state.settlement_system.audit_total_m2(expected_total=expected_money)

            # Track Economics
            if state.tracker:
                m0_dict = self.world_state.calculate_base_money()
                m0_pennies = m0_dict.get(DEFAULT_CURRENCY, 0)

                current_money_dollars = current_money / 100.0
                m2_leak_dollars = m2_leak_delta / 100.0

                state.tracker.track(
                    time=state.time,
                    households=state.households,
                    firms=state.firms,
                    markets=state.markets,
                    money_supply=current_money_dollars,
                    m2_leak=m2_leak_dollars,
                    monetary_base=float(m0_pennies)
                )

        # Market Panic Index
        total_deposits = 0
        if state.bank and hasattr(state.bank, "get_total_deposits_pennies"):
            total_deposits = state.bank.get_total_deposits_pennies()
        else:
            total_hh = sum(h.get_assets_by_currency().get(DEFAULT_CURRENCY, 0) for h in state.households)
            total_firm = sum(f.get_assets_by_currency().get(DEFAULT_CURRENCY, 0) for f in state.firms)
            total_deposits = int(total_hh + total_firm)

        try:
            is_positive_deposits = float(total_deposits) > 0
        except (TypeError, ValueError):
            is_positive_deposits = False

        if is_positive_deposits:
            try:
                # Need access to tick_withdrawal_pennies. It's on WorldState.
                raw_withdrawals = getattr(self.world_state, 'tick_withdrawal_pennies', 0)
                tick_withdrawals = float(raw_withdrawals)
                panic_index = tick_withdrawals / total_deposits
                self.world_state.market_panic_index = min(1.0, float(panic_index))
            except (TypeError, ValueError):
                self.world_state.market_panic_index = 0.0
        else:
            self.world_state.market_panic_index = 0.0

        logger.info(
            f"MARKET_PANIC_INDEX | Index: {self.world_state.market_panic_index:.4f}, Withdrawals: {getattr(self.world_state, 'tick_withdrawal_pennies', 0)}",
            extra={"tick": state.time, "panic_index": self.world_state.market_panic_index}
        )

        # Reset withdrawal counter for next tick
        if hasattr(self.world_state, 'tick_withdrawal_pennies'):
            self.world_state.tick_withdrawal_pennies = 0

        return state
