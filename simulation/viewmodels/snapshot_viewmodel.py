from typing import Dict, Any, List, Optional
import logging

from simulation.engine import Simulation
from simulation.db.repository import SimulationRepository
from simulation.dtos import (
    DashboardSnapshotDTO,
    DashboardGlobalIndicatorsDTO,
    SocietyTabDataDTO,
    GovernmentTabDataDTO,
    MarketTabDataDTO,
    FinanceTabDataDTO,
    GenerationStatDTO
)
from simulation.core_agents import Household
from simulation.metrics.inequality_tracker import InequalityTracker

logger = logging.getLogger(__name__)

class SnapshotViewModel:
    """
    Dashboard Snapshot을 생성하는 ViewModel입니다.
    """

    def __init__(self, repository: SimulationRepository):
        self.repository = repository
        self._cached_snapshot: Optional[DashboardSnapshotDTO] = None
        self._last_cached_tick: int = -1

    def get_dashboard_snapshot(self, simulation: Simulation, current_tick: int) -> DashboardSnapshotDTO:
        """
        현재 시뮬레이션 상태에 대한 DashboardSnapshotDTO를 생성합니다.
        성능 최적화:
         - HUD (Global Indicators): 매 틱 갱신 (실시간성)
         - Tabs (Society, Government, etc): 5틱마다 갱신 (Caching)
        """
        # 1. Global Indicators (HUD) - Always Fresh
        global_indicators = self._get_global_indicators(simulation, current_tick)

        # Caching logic for Tabs
        if self._cached_snapshot and current_tick - self._last_cached_tick < 5:
            # Reuse cached tabs but inject fresh global indicators and tick
            snapshot_copy = self._cached_snapshot
            snapshot_copy.tick = current_tick
            snapshot_copy.global_indicators = global_indicators
            return snapshot_copy

        # 2. Society Tab
        society_data = self._get_society_data(simulation, current_tick)

        # 3. Government Tab
        government_data = self._get_government_data(simulation, current_tick)

        # 4. Market Tab
        market_data = self._get_market_data(simulation, current_tick)

        # 5. Finance Tab
        finance_data = self._get_finance_data(simulation, current_tick)

        # Assemble Tabs
        tabs = {
            "society": society_data,
            "government": government_data,
            "market": market_data,
            "finance": finance_data
        }

        # Create full snapshot for cache
        self._cached_snapshot = DashboardSnapshotDTO(
            tick=current_tick,
            global_indicators=global_indicators,
            tabs=tabs
        )
        self._last_cached_tick = current_tick

        return self._cached_snapshot

    def _get_global_indicators(self, simulation: Simulation, current_tick: int) -> DashboardGlobalIndicatorsDTO:
        latest_indicators = simulation.tracker.get_latest_indicators()

        # Basic Metrics
        gdp = latest_indicators.get("total_consumption", 0.0)
        avg_wage = latest_indicators.get("avg_wage", 0.0)
        employment_rate = 100 - latest_indicators.get("unemployment_rate", 0.0)

        # Inequality (Gini)
        wealth_dist = simulation.inequality_tracker.calculate_wealth_distribution(simulation.households, simulation.stock_market)
        gini = wealth_dist.get("gini_total_assets", 0.0)

        # Attrition Rates
        start_tick = max(0, current_tick - 5)
        attrition_counts = self.repository.agents.get_attrition_counts(start_tick, current_tick, run_id=simulation.run_id)

        bankruptcy_count = attrition_counts.get("bankruptcy_count", 0)
        death_count = attrition_counts.get("death_count", 0)

        current_firms = len(simulation.firms)
        current_households = len(simulation.households)

        total_firms_window = current_firms + bankruptcy_count
        bankruptcy_rate = (bankruptcy_count / total_firms_window * 100.0) if total_firms_window > 0 else 0.0

        total_households_window = current_households + death_count
        death_rate = (death_count / total_households_window * 100.0) if total_households_window > 0 else 0.0

        # --- Phase 5: New Metrics ---
        # 1. Avg Tax Rate
        # Calculated as (Total Tax Collected This Tick) / (GDP This Tick)
        # We need tick-level tax collected. Government now tracks this history.
        last_tick_tax = 0.0
        if simulation.government.tax_history:
             last_tick_stats = simulation.government.tax_history[-1]
             if last_tick_stats["tick"] == current_tick:
                  last_tick_tax = last_tick_stats.get("total", 0.0)
             else:
                  # Maybe the government hasn't finalized this tick yet when this runs?
                  # Or this runs after finalize?
                  # If snapshot is called after run_tick, we should check the last entry.
                  # If tick mismatch, maybe previous tick.
                  last_tick_tax = last_tick_stats.get("total", 0.0) # Use latest available

        avg_tax_rate = (last_tick_tax / gdp) if gdp > 0 else 0.0

        # 2. Leisure Stats
        total_leisure_hours = 0.0
        total_parenting_hours = 0.0
        active_household_count = 0

        for h in simulation.households:
             if h.is_active:
                  leisure = simulation.household_time_allocation.get(h.id, 0.0)
                  total_leisure_hours += leisure
                  active_household_count += 1
                  if h.last_leisure_type == "PARENTING":
                       total_parenting_hours += leisure

        avg_leisure_hours = (total_leisure_hours / active_household_count) if active_household_count > 0 else 0.0
        parenting_rate = (total_parenting_hours / total_leisure_hours * 100.0) if total_leisure_hours > 0 else 0.0

        return DashboardGlobalIndicatorsDTO(
            death_rate=death_rate,
            bankruptcy_rate=bankruptcy_rate,
            employment_rate=employment_rate,
            gdp=gdp,
            avg_wage=avg_wage,
            gini=gini,
            avg_tax_rate=avg_tax_rate,
            avg_leisure_hours=avg_leisure_hours,
            parenting_rate=parenting_rate
        )

    def _get_society_data(self, simulation: Simulation, current_tick: int) -> SocietyTabDataDTO:
        # Generation Stats
        gen_stats_raw = self.repository.agents.get_generation_stats(current_tick, run_id=simulation.run_id)
        generations = [
            GenerationStatDTO(
                gen=row["gen"],
                count=row["count"],
                avg_assets=row["avg_assets"]
            ) for row in gen_stats_raw
        ]

        # Mitosis Cost
        current_pop = len([h for h in simulation.households if h.is_active])
        target_pop = simulation.config_module.TARGET_POPULATION
        base_threshold = simulation.config_module.MITOSIS_BASE_THRESHOLD
        sensitivity = simulation.config_module.MITOSIS_SENSITIVITY

        pop_ratio = current_pop / max(1, target_pop)
        mitosis_cost = base_threshold * (pop_ratio ** sensitivity)

        # Unemployment Pie & Time Allocation
        struggling = 0
        voluntary = 0

        # Time Allocation Aggregation
        time_allocation = {
             "WORK": 0.0,
             "PARENTING": 0.0,
             "SELF_DEV": 0.0,
             "ENTERTAINMENT": 0.0,
             "IDLE": 0.0
        }
        total_leisure_sum = 0.0
        count_active = 0

        for h in simulation.households:
            if h.is_active:
                count_active += 1
                # Unemployment Logic
                if not h.is_employed:
                    survival_need = h.needs.get("survival", 0.0)
                    if survival_need > 50:
                        struggling += 1
                    else:
                        voluntary += 1

                # Time Allocation Logic
                leisure_hours = simulation.household_time_allocation.get(h.id, 0.0)
                work_hours = getattr(simulation.config_module, "HOURS_PER_TICK", 24.0) - getattr(simulation.config_module, "SHOPPING_HOURS", 2.0) - leisure_hours

                time_allocation["WORK"] += work_hours

                l_type = h.last_leisure_type
                if l_type in time_allocation:
                     time_allocation[l_type] += leisure_hours
                else:
                     time_allocation["IDLE"] += leisure_hours # Fallback

                total_leisure_sum += leisure_hours

        unemployment_pie = {
            "struggling": struggling,
            "voluntary": voluntary
        }

        avg_leisure_hours = (total_leisure_sum / count_active) if count_active > 0 else 0.0

        return SocietyTabDataDTO(
            generations=generations,
            mitosis_cost=mitosis_cost,
            unemployment_pie=unemployment_pie,
            time_allocation=time_allocation,
            avg_leisure_hours=avg_leisure_hours,
            avg_education_level=simulation.tracker.get_latest_indicators().get("avg_education_level", 0.0),
            brain_waste_count=int(simulation.tracker.get_latest_indicators().get("brain_waste_count", 0))
        )

    def _get_government_data(self, simulation: Simulation, current_tick: int) -> GovernmentTabDataDTO:
        # Accumulated Stats
        tax_revenue = simulation.government.tax_revenue.copy()
        # Fiscal Balance
        fiscal_balance = {
            "revenue": simulation.government.total_collected_tax,
            "expense": simulation.government.total_spent_subsidies + (simulation.government.infrastructure_level * getattr(simulation.config_module, "INFRASTRUCTURE_INVESTMENT_COST", 5000.0)) # Approx
        }

        # Phase 5: Historical Data
        tax_history = simulation.government.tax_history
        welfare_history = simulation.government.welfare_history

        # Current Stats
        # Use latest history point or current_tick_stats (which is reset at tick end, so might be empty if called after finalize)
        # Snapshot is usually called after tick is done.
        current_welfare = 0.0
        current_avg_tax_rate = 0.0

        if tax_history:
             last = tax_history[-1]
             # Calculate rate relative to GDP
             gdp = simulation.tracker.get_latest_indicators().get("total_consumption", 1.0)
             current_avg_tax_rate = (last.get("total", 0.0) / gdp) if gdp > 0 else 0.0

        if welfare_history:
             last_w = welfare_history[-1]
             current_welfare = last_w.get("welfare", 0.0) + last_w.get("stimulus", 0.0)

        return GovernmentTabDataDTO(
            tax_revenue=tax_revenue,
            fiscal_balance=fiscal_balance,
            tax_revenue_history=tax_history,
            welfare_spending=current_welfare,
            current_avg_tax_rate=current_avg_tax_rate,
            welfare_history=welfare_history,
            education_spending=simulation.government.current_tick_stats.get("education_spending", 0.0) if hasattr(simulation.government, "education_history") else 0.0,
            education_history=getattr(simulation.government, "education_history", [])
        )

    def _get_market_data(self, simulation: Simulation, current_tick: int) -> MarketTabDataDTO:
        # Commodity Volumes (Current Tick)
        commodity_volumes = {}
        # Fetch from markets
        for name, market in simulation.markets.items():
            if hasattr(market, 'get_daily_volume'):
                 commodity_volumes[name] = market.get_daily_volume()

        # History Window
        WINDOW_SIZE = 50
        start_tick = max(0, current_tick - WINDOW_SIZE)

        history_data = self.repository.analytics.get_economic_indicators(start_tick, current_tick, run_id=simulation.run_id)

        # CPI: Weighted Average of Goods Prices
        # In `EconomicIndicatorData`, we have `avg_goods_price` (which is weighted avg of goods).
        # We also have `food_avg_price`.
        # Let's use `avg_goods_price` as CPI proxy.
        cpi = [row["avg_goods_price"] if row["avg_goods_price"] else 0.0 for row in history_data]

        # Maslow Fulfillment: 100 - avg_survival_need
        # We need `avg_survival_need` from history.
        maslow_fulfillment = []
        for row in history_data:
            avg_survival = row.get("avg_survival_need") or 0.0
            maslow_fulfillment.append(max(0.0, 100.0 - avg_survival))

        return MarketTabDataDTO(
            commodity_volumes=commodity_volumes,
            cpi=cpi,
            maslow_fulfillment=maslow_fulfillment
        )

    def _get_finance_data(self, simulation: Simulation, current_tick: int) -> FinanceTabDataDTO:
        stock_market = simulation.stock_market

        market_cap = 0.0
        volume = 0.0
        turnover = 0.0
        dividend_yield = 0.0 # Placeholder

        if stock_market:
            # Market Cap = Sum(Price * Total Shares)
            # We need current prices and total shares for all firms.
            # StockMarket doesn't store total shares, Firms do.
            for firm in simulation.firms:
                if firm.is_active:
                    price = stock_market.get_stock_price(firm.id) or 0.0 # get_stock_price handles None? It returns Optional[float]
                    # If None (no trade), use last trade or reference?
                    # StockMarket.get_stock_price returns last trade price or None.
                    if price == 0.0:
                         # Fallback to daily avg or reference
                         price = stock_market.get_daily_avg_price(firm.id)

                    market_cap += price * firm.total_shares

            # Volume (Daily)
            # StockMarket is a Market subclass? It has `get_daily_volume()`?
            # StockMarket inherits from OrderBookMarket? No, from Market directly?
            # Let's check StockMarket implementation.
            # Assuming it aggregates volume across all tickers or we sum up.
            # Simulation code calls `stock_market.match_orders` which likely returns transactions.
            # Does `stock_market` have a total volume counter?
            # Usually `get_daily_volume()` on Market returns volume for that market.
            # If StockMarket handles multiple items (tickers), does it sum them?
            # Let's assume yes or iterate firms if needed.
            # `market_data` logic in engine calls `stock_market.get_daily_volume()`? No, it calls per firm?
            # I will check StockMarket code if needed. For now, assume a method exists or sum manually.
            pass

            # Volume aggregation manually if get_daily_volume isn't global
            # Actually, `StockMarket` has `daily_trade_volume` dict by firm_id?
            # I'll check `stock_tracker` or `stock_market` instance.
            # Safe bet: Iterate firms and sum volumes if `stock_market` methods are per-firm.
            # But `market.get_daily_volume()` is abstract in `Market`.

            # Volume (Daily)
            if hasattr(stock_market, 'get_daily_volume'):
                 volume = stock_market.get_daily_volume()

            # For Turnover: Volume / Total Outstanding Shares?
            # Total shares in market = Sum(firm.total_shares)
            total_shares_market = sum(f.total_shares for f in simulation.firms if f.is_active)
            if total_shares_market > 0:
                 turnover = (volume / total_shares_market) * 100.0 # Percentage

        return FinanceTabDataDTO(
            market_cap=market_cap,
            volume=volume,
            turnover=turnover,
            dividend_yield=dividend_yield
        )
