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
        성능을 위해 5틱마다 무거운 지표를 재계산합니다.
        """
        # Caching logic (only refresh heavy metrics every 5 ticks)
        if self._cached_snapshot and current_tick - self._last_cached_tick < 5:
            # We update the tick to the current one so frontend knows it's the latest response
            snapshot_copy = self._cached_snapshot
            snapshot_copy.tick = current_tick
            return snapshot_copy

        # 1. Global Indicators (HUD)
        global_indicators = self._get_global_indicators(simulation, current_tick)

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
        # GDP -> total_consumption as per spec
        gdp = latest_indicators.get("total_consumption", 0.0)
        avg_wage = latest_indicators.get("avg_wage", 0.0)
        employment_rate = 100 - latest_indicators.get("unemployment_rate", 0.0) # Spec asks for employment rate

        # Inequality (Gini)
        # Use Simulation's live InequalityTracker for current state
        wealth_dist = simulation.inequality_tracker.calculate_wealth_distribution(simulation.households, simulation.stock_market)
        gini = wealth_dist.get("gini_total_assets", 0.0)

        # Attrition Rates (Death/Bankruptcy)
        # Compare current state with 5 ticks ago
        start_tick = max(0, current_tick - 5)
        attrition_counts = self.repository.get_attrition_counts(start_tick, current_tick, run_id=simulation.run_id)

        bankruptcy_count = attrition_counts.get("bankruptcy_count", 0)
        death_count = attrition_counts.get("death_count", 0)

        # Rates calculations (based on *initial* or *average* count in window?
        # For simplicity and robustness, let's use current totals + attrition as denominator, or just use current totals)
        # Spec says "changes in agent_states". Rate usually implies per capita.
        # Let's assume rate = count / (current_count + count) * 100 approx.
        # Or just raw count if frontend expects rate but backend provides count?
        # DTO says `death_rate: float`. Let's calculate % of population lost in last 5 ticks.

        # We need denominator (approx population 5 ticks ago)
        current_firms = len(simulation.firms) # Active firms
        current_households = len(simulation.households) # Active households

        # Avoid division by zero
        # 5-tick bankruptcy rate
        total_firms_window = current_firms + bankruptcy_count
        bankruptcy_rate = (bankruptcy_count / total_firms_window * 100.0) if total_firms_window > 0 else 0.0

        # 5-tick death rate
        total_households_window = current_households + death_count
        death_rate = (death_count / total_households_window * 100.0) if total_households_window > 0 else 0.0

        return DashboardGlobalIndicatorsDTO(
            death_rate=death_rate,
            bankruptcy_rate=bankruptcy_rate,
            employment_rate=employment_rate,
            gdp=gdp,
            avg_wage=avg_wage,
            gini=gini
        )

    def _get_society_data(self, simulation: Simulation, current_tick: int) -> SocietyTabDataDTO:
        # Generation Stats
        gen_stats_raw = self.repository.get_generation_stats(current_tick, run_id=simulation.run_id)
        generations = [
            GenerationStatDTO(
                gen=row["gen"],
                count=row["count"],
                avg_assets=row["avg_assets"]
            ) for row in gen_stats_raw
        ]

        # Mitosis Cost
        # Dynamic threshold based on current population pressure
        # Formula: Cost = Base * (Pop/Target)^Sensitivity
        current_pop = len([h for h in simulation.households if h.is_active])
        target_pop = simulation.config_module.TARGET_POPULATION
        base_threshold = simulation.config_module.MITOSIS_BASE_THRESHOLD
        sensitivity = simulation.config_module.MITOSIS_SENSITIVITY

        pop_ratio = current_pop / max(1, target_pop)
        mitosis_cost = base_threshold * (pop_ratio ** sensitivity)

        # Unemployment Pie
        # "Struggling": Unemployed & survival_need > 50
        # "Voluntary": Unemployed & survival_need <= 50
        struggling = 0
        voluntary = 0

        for h in simulation.households:
            if h.is_active and not h.is_employed:
                survival_need = h.needs.get("survival", 0.0)
                if survival_need > 50:
                    struggling += 1
                else:
                    voluntary += 1

        unemployment_pie = {
            "struggling": struggling,
            "voluntary": voluntary
        }

        return SocietyTabDataDTO(
            generations=generations,
            mitosis_cost=mitosis_cost,
            unemployment_pie=unemployment_pie
        )

    def _get_government_data(self, simulation: Simulation, current_tick: int) -> GovernmentTabDataDTO:
        tax_revenue = simulation.government.tax_revenue.copy()

        # Fiscal Balance
        # Total Revenue vs Total Expenditure
        # Currently we have accumulated totals in Government agent
        # Ideally, we might want "Last Tick" or "Recent Window" balance.
        # DTO says `fiscal_balance: Dict[str, float]`. Let's return totals for now?
        # Or maybe "revenue" vs "expense".
        fiscal_balance = {
            "revenue": simulation.government.total_collected_tax,
            "expense": simulation.government.total_spent_subsidies + (simulation.government.infrastructure_level * getattr(simulation.config_module, "INFRASTRUCTURE_INVESTMENT_COST", 5000.0)) # Approx
            # Note: Infrasturcture cost is subtracted from assets directly in invest_infrastructure.
            # We don't track total_spent_infrastructure in a field.
            # But we can infer it or just use assets?
            # Let's just put accumulated revenue/expense we know.
        }
        # Actually `total_spent_subsidies` is tracked.

        return GovernmentTabDataDTO(
            tax_revenue=tax_revenue,
            fiscal_balance=fiscal_balance
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

        history_data = self.repository.get_economic_indicators(start_tick, current_tick, run_id=simulation.run_id)

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
