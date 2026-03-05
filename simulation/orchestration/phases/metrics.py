from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState
from modules.system.api import DEFAULT_CURRENCY
from modules.analytics.api import EconomyAnalyticsSnapshotDTO, HouseholdAnalyticsDTO, FirmAnalyticsDTO, MarketAnalyticsDTO


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

                # Assemble DTOs
                household_dtos = []
                for h in state.households:
                    h_is_active = h._bio_state.is_active
                    h_cash_pennies = int(state.tracker._calculate_total_wallet_value(h._econ_state.assets)) if h_is_active else 0

                    stock_val = 0.0
                    stock_market = state.markets.get("stock_market")
                    if h_is_active and stock_market and hasattr(stock_market, 'get_stock_price'):
                        for firm_id, holding in h._econ_state.portfolio.holdings.items():
                            if holding.quantity > 0:
                                price = stock_market.get_stock_price(firm_id) or 0.0
                                stock_val += holding.quantity * price

                    household_dtos.append(HouseholdAnalyticsDTO(
                        agent_id=h.id,
                        is_active=h_is_active,
                        total_cash_pennies=h_cash_pennies,
                        portfolio_value_pennies=int(stock_val * 100) if stock_val else 0,
                        is_employed=getattr(h._econ_state, 'is_employed', False),
                        trust_score=getattr(h._social_state, 'trust_score', 0.5) if hasattr(h, '_social_state') else 0.5,
                        survival_need=h._bio_state.needs.get('survival', 0.0) if hasattr(h, '_bio_state') else 0.0,
                        consumption_expenditure_pennies=getattr(h._econ_state, 'consumption_expenditure_this_tick_pennies', 0),
                        food_expenditure_pennies=getattr(h._econ_state, 'food_expenditure_this_tick_pennies', 0),
                        labor_income_pennies=getattr(h._econ_state, 'labor_income_this_tick_pennies', 0),
                        education_level=getattr(h._econ_state, 'education_level', 0.0),
                        aptitude=getattr(h._econ_state, 'aptitude', 0.0)
                    ))

                firm_dtos = []
                for f in state.firms:
                    f_is_active = getattr(f, "is_active", False)
                    f_cash_pennies = 0
                    f_total_assets_pennies = 0
                    if f_is_active:
                        if hasattr(f, "get_all_balances"):
                            f_cash_pennies = int(state.tracker._calculate_total_wallet_value(f.get_all_balances()))
                            usd_cash = f.get_balance(DEFAULT_CURRENCY)
                        elif hasattr(f, "assets"):
                            assets = f.assets
                            if isinstance(assets, dict):
                                f_cash_pennies = int(state.tracker._calculate_total_wallet_value(assets))
                                usd_cash = assets.get(DEFAULT_CURRENCY, 0.0)
                            else:
                                f_cash_pennies = int(assets)
                                usd_cash = assets
                        else:
                            f_cash_pennies = 0
                            usd_cash = 0.0

                        if hasattr(f, "get_financial_snapshot"):
                            snap = f.get_financial_snapshot()
                            snap_total_assets = snap.get("total_assets", 0.0)
                            non_cash_assets = snap_total_assets - usd_cash
                            f_total_assets_pennies = f_cash_pennies + int(non_cash_assets)
                        else:
                            f_total_assets_pennies = f_cash_pennies

                    firm_dtos.append(FirmAnalyticsDTO(
                        agent_id=f.id,
                        is_active=f_is_active,
                        total_assets_pennies=f_total_assets_pennies,
                        cash_balance_pennies=f_cash_pennies,
                        current_production=getattr(f, "current_production", 0.0),
                        inventory_volume=sum(f.get_all_items().values()) if hasattr(f, "get_all_items") and f.get_all_items() else 0.0,
                        sales_volume=getattr(f, "sales_volume_this_tick", 0.0)
                    ))

                market_dtos = []
                for market_id, market in state.markets.items():
                    market_dtos.append(MarketAnalyticsDTO(
                        market_id=market_id,
                        avg_price=market.get_daily_avg_price() if hasattr(market, "get_daily_avg_price") else getattr(market, "avg_price", 0.0),
                        volume=market.get_daily_volume() if hasattr(market, "get_daily_volume") else getattr(market, "volume", 0.0),
                        current_price=getattr(market, "current_price", 0.0)
                    ))

                snapshot = EconomyAnalyticsSnapshotDTO(
                    tick=state.time,
                    households=household_dtos,
                    firms=firm_dtos,
                    markets=market_dtos,
                    money_supply_pennies=current_money,
                    m2_leak_pennies=int(m2_leak_delta),
                    monetary_base_pennies=int(m0_pennies)
                )

                state.tracker.track_tick(snapshot)

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
