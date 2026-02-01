from __future__ import annotations
from typing import Dict, Any, TYPE_CHECKING
import math
import logging

from simulation.markets.order_book_market import OrderBookMarket
from modules.system.api import (
    MarketSignalDTO, MarketSnapshotDTO,
    HousingMarketSnapshotDTO, LoanMarketSnapshotDTO, LaborMarketSnapshotDTO,
    HousingMarketUnitDTO
)
from simulation.dtos.api import (
    SimulationState, DecisionInputDTO, GovernmentPolicyDTO, MacroFinancialContext,
    FiscalContext
)
from modules.government.proxy import GovernmentFiscalProxy

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class MarketSignalFactory:
    def create_market_signals(self, markets: Dict[str, Any]) -> Dict[str, MarketSignalDTO]:
        market_signals: Dict[str, MarketSignalDTO] = {}

        for m_id, market in markets.items():
            # Only process OrderBookMarkets that have items
            if isinstance(market, OrderBookMarket):
                # Identify all unique items in this market (buy or sell side)
                all_items = set(market.buy_orders.keys()) | set(market.sell_orders.keys()) | set(market.last_traded_prices.keys())

                for item_id in all_items:
                     price_history = list(market.price_history.get(item_id, []))
                     # Take last 7 ticks or less
                     history_7d = price_history[-7:]

                     # Volatility Calculation
                     volatility = 0.0
                     if len(history_7d) > 1:
                         mean = sum(history_7d) / len(history_7d)
                         variance = sum((p - mean) ** 2 for p in history_7d) / len(history_7d)
                         volatility = math.sqrt(variance)

                     # Check frozen status
                     is_frozen = False

                     # Calculate total quantities
                     total_bid_quantity = sum(order.quantity for order in market.buy_orders.get(item_id, []))
                     total_ask_quantity = sum(order.quantity for order in market.sell_orders.get(item_id, []))

                     signal = MarketSignalDTO(
                         market_id=m_id,
                         item_id=item_id,
                         best_bid=market.get_best_bid(item_id),
                         best_ask=market.get_best_ask(item_id),
                         last_traded_price=market.get_last_traded_price(item_id),
                         last_trade_tick=market.get_last_trade_tick(item_id) or -1,
                         price_history_7d=history_7d,
                         volatility_7d=volatility,
                         order_book_depth_buy=len(market.buy_orders.get(item_id, [])),
                         order_book_depth_sell=len(market.sell_orders.get(item_id, [])),
                         total_bid_quantity=total_bid_quantity,
                         total_ask_quantity=total_ask_quantity,
                         is_frozen=is_frozen
                     )
                     market_signals[item_id] = signal
        return market_signals

class MarketSnapshotFactory:
    def __init__(self, signal_factory: MarketSignalFactory):
        self.signal_factory = signal_factory

    def create_snapshot(self, state: SimulationState) -> MarketSnapshotDTO:
        # 1. Create Signals
        market_signals = self.signal_factory.create_market_signals(state.markets)

        # 2. Extract Housing Data
        housing_market = state.markets.get("housing")
        for_sale_units = []

        # Pre-fetch unit qualities if available
        unit_quality_map = {}
        if hasattr(state, "real_estate_units") and state.real_estate_units:
             for u in state.real_estate_units:
                 if hasattr(u, "id") and hasattr(u, "quality_score"):
                     unit_quality_map[u.id] = u.quality_score

        if housing_market and hasattr(housing_market, "sell_orders"):
             for item_id, sell_orders in housing_market.sell_orders.items():
                if item_id.startswith("unit_") and sell_orders:
                    order = sell_orders[0] # Best price (OrderBookMarket sorts by price)
                    quality = unit_quality_map.get(item_id, 1.0)

                    for_sale_units.append(HousingMarketUnitDTO(
                        unit_id=item_id,
                        price=order.price,
                        quality=quality
                    ))

        housing_data = state.market_data.get("housing_market", {})
        housing_snapshot = HousingMarketSnapshotDTO(
            for_sale_units=for_sale_units,
            avg_rent_price=housing_data.get("avg_rent_price", 100.0),
            avg_sale_price=housing_data.get("avg_sale_price", 24000.0)
        )

        # 3. Extract Loan Data
        loan_data = state.market_data.get("loan_market", {})
        loan_snapshot = LoanMarketSnapshotDTO(
            interest_rate=loan_data.get("interest_rate", 0.05)
        )

        # 4. Extract Labor Data
        labor_data = state.market_data.get("labor", {})
        labor_snapshot = LaborMarketSnapshotDTO(
            avg_wage=labor_data.get("avg_wage", 0.0)
        )

        return MarketSnapshotDTO(
            tick=state.time,
            market_signals=market_signals,
            housing=housing_snapshot,
            loan=loan_snapshot,
            labor=labor_snapshot,
            market_data=state.market_data
        )

class DecisionInputFactory:
    def create_decision_input(
        self,
        state: SimulationState,
        world_state: WorldState,
        market_snapshot: MarketSnapshotDTO
    ) -> DecisionInputDTO:

        gov = state.government
        bank = state.bank
        gov_policy = GovernmentPolicyDTO(
             income_tax_rate=getattr(gov, "income_tax_rate", 0.1),
             sales_tax_rate=getattr(state.config_module, "SALES_TAX_RATE", 0.05),
             corporate_tax_rate=getattr(gov, "corporate_tax_rate", 0.2),
             base_interest_rate=getattr(bank, "base_rate", 0.05) if bank else 0.05
        )

        # Create Fiscal Context
        gov_proxy = GovernmentFiscalProxy(gov) if gov else None
        fiscal_context = FiscalContext(government=gov_proxy) if gov_proxy else None

        macro_financial_context = None
        if getattr(state.config_module, "MACRO_PORTFOLIO_ADJUSTMENT_ENABLED", False):
            interest_rate_trend = 0.0
            if bank:
                interest_rate_trend = bank.base_rate - world_state.last_interest_rate
                world_state.last_interest_rate = bank.base_rate

            market_volatility = world_state.stock_tracker.get_market_volatility() if world_state.stock_tracker else 0.0

            macro_financial_context = MacroFinancialContext(
                inflation_rate=0.0, # Placeholder as per original
                gdp_growth_rate=0.0, # Placeholder as per original
                market_volatility=market_volatility,
                interest_rate_trend=interest_rate_trend
            )

        # Prepare Agent Registry (WO-138)
        agent_registry = {}
        if state.government:
            agent_registry["GOVERNMENT"] = state.government.id
        if state.central_bank:
            agent_registry["CENTRAL_BANK"] = state.central_bank.id
        if state.bank:
             agent_registry["BANK"] = state.bank.id

        return DecisionInputDTO(
             # markets=state.markets,  <-- REMOVED
             goods_data=state.goods_data,
             market_data=state.market_data,
             current_time=state.time,
             fiscal_context=fiscal_context,
             market_snapshot=market_snapshot,
             government_policy=gov_policy,
             agent_registry=agent_registry,
             stress_scenario_config=world_state.stress_scenario_config,
             macro_context=macro_financial_context
        )
