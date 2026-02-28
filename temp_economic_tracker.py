from __future__ import annotations
from typing import List, Dict, Any, TYPE_CHECKING, Mapping, Optional
import logging
import statistics
from collections import deque

if TYPE_CHECKING:
    from simulation.world_state import WorldState

from simulation.dtos.api import MarketContextDTO
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.core_markets import Market
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode
from modules.finance.exchange.engine import CurrencyExchangeEngine

logger = logging.getLogger(__name__)


class EconomicIndicatorTracker:
    """경제 시뮬레이션의 주요 지표들을 추적하고 기록하는 클래스.

    매 틱마다 가계, 기업, 시장 데이터를 기반으로 실업률, 평균 가격, 총 자산 등을 계산하고 저장합니다.
    """

    def __init__(self, config_module: Any) -> None:
        """EconomicIndicatorTracker를 초기화합니다.

        metrics: 추적할 경제 지표들을 저장하는 딕셔너리.
        config_module: 시뮬레이션 설정을 담고 있는 모듈.
        all_fieldnames: CSV 파일 저장 시 사용될 모든 필드 이름 리스트 (이제 사용되지 않음).
        """
        self.metrics: Dict[str, List[float]] = {
            "goods_price_index": [],
            "unemployment_rate": [],
            "avg_wage": [],
            "money_supply": [],
            "monetary_base": [],
            "total_labor_income": [],
            "total_sales_volume": [],
            # TD-015: New Centralized Metrics
            "gdp": [],
            "gini": [],
            "social_cohesion": [],
            "active_population": [],
            # Population Distribution (Quintiles) - stored as individual series or flattened
            "quintile_1_avg_assets": [],
            "quintile_2_avg_assets": [],
            "quintile_3_avg_assets": [],
            "quintile_4_avg_assets": [],
            "quintile_5_avg_assets": [],
        }

        # Watchtower Hardening: SMA History (Window=50)
        self.history_window = 50
        self.gdp_history: deque[float] = deque(maxlen=self.history_window)
        self.cpi_history: deque[float] = deque(maxlen=self.history_window)
        self.m2_leak_history: deque[float] = deque(maxlen=self.history_window)

        self.config_module = config_module  # Store config_module
        self.exchange_engine = CurrencyExchangeEngine(config_module) # TD-213: Initialize Exchange Engine

        self.all_fieldnames: List[
            str
        ] = [  # Keep for record structure, but not for CSV writing
            "time",
            "total_household_assets",
            "total_firm_assets",
            "unemployment_rate",
            "food_avg_price",
            "food_trade_volume",
            "avg_goods_price",
            "avg_wage",
            "total_production",
            "total_consumption",
            "total_food_consumption",
            "total_inventory",
            "avg_survival_need",
            "gdp", # Added
            "gini", # Added
            "social_cohesion", # Added
        ]
        self.logger = logging.getLogger(__name__)

    def capture_market_context(self) -> MarketContextDTO:
        """
        Captures the current exchange rates and other global market context.
        Tick-Snapshot Injection to ensure O(1) access for AI agents.
        """
        exchange_rates = self.exchange_engine.get_all_rates()
        # Initial empty benchmark rates as placeholders
        return MarketContextDTO(
            exchange_rates=exchange_rates,
            benchmark_rates={}
        )

    def _calculate_total_wallet_value(self, wallet_dict: Mapping[CurrencyCode, float | int]) -> float:
        """
        TD-213: Calculates total value of a wallet in DEFAULT_CURRENCY.
        Iterates over all currencies and converts them using CurrencyExchangeEngine.
        """
        total = 0.0
        if not wallet_dict:
            return 0.0

        # Optimize: if only DEFAULT_CURRENCY exists
        if len(wallet_dict) == 1 and DEFAULT_CURRENCY in wallet_dict:
            return float(wallet_dict[DEFAULT_CURRENCY])

        for currency, amount in wallet_dict.items():
            if amount == 0: continue
            total += self.exchange_engine.convert(float(amount), currency, DEFAULT_CURRENCY)
        return total

    def calculate_gini_coefficient(self, values: List[float]) -> float:
        """
        TD-015: Calculate Gini coefficient.
        """
        if not values or len(values) < 2:
            return 0.0

        n = len(values)
        sorted_values = sorted(values)

        if sum(sorted_values) == 0:
            return 0.0

        cumsum = sum((i + 1) * x for i, x in enumerate(sorted_values))
        total = sum(sorted_values)

        gini = (2 * cumsum - (n + 1) * total) / (n * total)
        return max(0.0, min(1.0, gini))

    def calculate_social_cohesion(self, households: List[Household]) -> float:
        """
        TD-015: Calculate Social Cohesion based on average Trust Score of active households.
        """
        active_households = [h for h in households if h._bio_state.is_active]
        if not active_households:
            return 0.5 # Default neutral

        total_trust = sum(h._social_state.trust_score for h in active_households)
        return total_trust / len(active_households)

    def calculate_population_metrics(self, households: List[Household], markets: Optional[Dict[str, Market]] = None) -> Dict[str, Any]:
        """
        TD-015: Calculate Population Metrics (Distribution, Active Count).
        Returns a dictionary with 'distribution' (quintiles) and 'active_count'.
        Now includes Stock Portfolio value in Total Assets.
        """
        active_households = [h for h in households if h._bio_state.is_active]
        active_count = len(active_households)

        if not active_households:
            return {
                "active_count": 0,
                "distribution": {f"q{i}": 0.0 for i in range(1, 6)},
                "all_assets": []
            }

        stock_market = markets.get("stock_market") if markets else None

        # Calculate assets for Gini
        all_assets = []
        for h in active_households:
             # 1. Cash (Wallet)
             cash_val = self._calculate_total_wallet_value(h._econ_state.assets)

             # 2. Portfolio (Stocks)
             stock_val = 0.0
             if stock_market and hasattr(stock_market, 'get_stock_price'):
                 for firm_id, holding in h._econ_state.portfolio.holdings.items():
                     if holding.quantity > 0:
                         price = stock_market.get_stock_price(firm_id) or 0.0
                         stock_val += holding.quantity * price

             all_assets.append(cash_val + stock_val)

        sorted_assets = sorted(all_assets)

        # Quintiles (Average Assets per Quintile)
        n = len(sorted_assets)
        quintile_size = max(1, n // 5)

        distribution = {}
        for i in range(5):
            start = i * quintile_size
            end = (i + 1) * quintile_size if i < 4 else n
            q_slice = sorted_assets[start:end]
            avg = statistics.mean(q_slice) if q_slice else 0.0
            distribution[f"q{i+1}"] = avg

        return {
            "active_count": active_count,
            "distribution": distribution,
            "all_assets": all_assets
        }

    def track(
        self,
        time: int,
        households: List[Household],
        firms: List[Firm],
        markets: Dict[str, Market],
        money_supply: float = 0.0,
        m2_leak: float = 0.0,
        monetary_base: float = 0.0,
    ) -> None:
        """현재 시뮬레이션 틱의 경제 지표를 계산하고 기록합니다."""
        self.logger.debug(
            f"TRACKER_UPDATE | Starting tracker update for tick {time}",
            extra={"tick": time, "tags": ["tracker"]},
        )
        record: Dict[str, Any] = {"time": time}

        # WO-043: Track Money Supply
        record["money_supply"] = money_supply
        record["monetary_base"] = monetary_base

        # Perform calculations...
        # TD-213: Tracks all assets converted to DEFAULT_CURRENCY.
        # WO-IMPL-FINANCIAL-PRECISION: Cast to int (Pennies) for strict compliance
        total_household_assets = int(sum(
            self._calculate_total_wallet_value(h._econ_state.assets) for h in households if h._bio_state.is_active
        ))

        # WO-106: Initial Sink Fix
        total_firm_assets = 0
        for f in firms:
             if not getattr(f, "is_active", False):
                 continue

             if hasattr(f, "get_all_balances"):
                 firm_wallet_value = self._calculate_total_wallet_value(f.get_all_balances())
                 usd_cash_in_snapshot = f.get_balance(DEFAULT_CURRENCY)
             elif hasattr(f, "assets"):
                 # Legacy/Mock Fallback
                 assets = f.assets
                 if isinstance(assets, dict):
                     firm_wallet_value = self._calculate_total_wallet_value(assets)
                     usd_cash_in_snapshot = assets.get(DEFAULT_CURRENCY, 0.0)
                 else:
                     firm_wallet_value = assets
                     usd_cash_in_snapshot = assets
             else:
                 firm_wallet_value = 0.0
                 usd_cash_in_snapshot = 0.0

             if hasattr(f, "get_financial_snapshot"):
                 snap = f.get_financial_snapshot()
                 snap_total_assets = snap.get("total_assets", 0.0)
                 
                 non_cash_assets = snap_total_assets - usd_cash_in_snapshot
                 total_firm_assets += firm_wallet_value + non_cash_assets
             else:
                 total_firm_assets += firm_wallet_value

        # WO-IMPL-FINANCIAL-PRECISION: Ensure total_firm_assets is int
        total_firm_assets = int(total_firm_assets)

        record["total_household_assets"] = total_household_assets
        record["total_firm_assets"] = total_firm_assets

        total_households = len([h for h in households if h._bio_state.is_active])
        unemployed_households = 0
        for h in households:
            if h._bio_state.is_active:
                if not hasattr(h, '_econ_state') or not h._econ_state.is_employed:
                    unemployed_households += 1
        record["unemployment_rate"] = (
            (unemployed_households / total_households) * 100
            if total_households > 0
            else 0
        )

        # Market Data
        total_volume = 0.0
        weighted_price_sum = 0.0
        food_price_sum = 0.0
        food_volume_sum = 0.0
        primary_food_key = "basic_food"

        for market_id, market in markets.items():
            if market_id == "labor" or market_id == "loan_market" or market_id == "stock_market":
                continue

            if hasattr(market, "get_daily_avg_price"):
                avg_price = market.get_daily_avg_price()
                volume = market.get_daily_volume()

                if volume > 0:
                    weighted_price_sum += avg_price * volume
                    total_volume += volume

                if "food" in market_id:
                    if volume > 0:
                         food_price_sum += avg_price * volume
                         food_volume_sum += volume

        if food_volume_sum > 0:
            record["food_avg_price"] = int(food_price_sum / food_volume_sum)
        else:
            f_market = markets.get(primary_food_key)
            if f_market and hasattr(f_market, "get_daily_avg_price"):
                 record["food_avg_price"] = int(f_market.get_daily_avg_price() or 0)
            else:
                 record["food_avg_price"] = 0

        record["food_trade_volume"] = food_volume_sum

        if total_volume > 0:
            record["avg_goods_price"] = int(weighted_price_sum / total_volume)
        else:
            fallback_prices = []
            for market_id, market in markets.items():
                if market_id in ["labor", "loan_market", "stock_market", "housing"]:
                    continue
                price = getattr(market, "current_price", None)
                if price is None or price <= 0:
                    price = getattr(market, "avg_price", 0.0)
                if price > 0:
                    fallback_prices.append(price)

            if fallback_prices:
                record["avg_goods_price"] = int(sum(fallback_prices) / len(fallback_prices))
            else:
                record["avg_goods_price"] = 0

        # Sync to goods_price_index for CPI tracking
        record["goods_price_index"] = record["avg_goods_price"]

        # Production & Consumption
        total_production = sum(
            f.current_production
            for f in firms
            if getattr(f, "is_active", False)
        )
        record["total_production"] = total_production

        # WO-IMPL-FINANCIAL-PRECISION: Maintain Penny Standard (int)
        total_consumption = sum(
            h._econ_state.consumption_expenditure_this_tick_pennies for h in households if h._bio_state.is_active
        )
        record["total_consumption"] = int(total_consumption)

        # WO-IMPL-FINANCIAL-PRECISION: Maintain Penny Standard (int)
        total_food_consumption = sum(
            h._econ_state.food_expenditure_this_tick_pennies
            for h in households
            if isinstance(h, Household) and h._bio_state.is_active
        )
        record["total_food_consumption"] = int(total_food_consumption)

        total_inventory = sum(
            sum(f.get_all_items().values()) if f.get_all_items() else 0.0
            for f in firms
            if getattr(f, "is_active", False)
        )
        record["total_inventory"] = total_inventory

        # Avg Survival Need
        active_households_count = 0
        total_survival_need = 0.0
        for h in households:
            if h._bio_state.is_active:
                active_households_count += 1
                total_survival_need += h._bio_state.needs.get("survival", 0.0)

        record["avg_survival_need"] = (
            total_survival_need / active_households_count
            if active_households_count > 0 else 0.0
        )

        # --- WO-043: Comprehensive Metrics ---
        # 1. Labor Share
        # Sum labor income (pennies). Kept in pennies for reporting parity with GDP (Pennies).
        # WO-IMPL-FINANCIAL-PRECISION: Removed conversion to dollars.
        total_labor_income_pennies = sum(
            h._econ_state.labor_income_this_tick_pennies
            for h in households
            if h._bio_state.is_active
        )
        total_labor_income = total_labor_income_pennies
        record["total_labor_income"] = int(total_labor_income)

        # Sales Volume
        total_sales_volume = sum(
            getattr(f, "sales_volume_this_tick", 0.0) for f in firms
        )
        record["total_sales_volume"] = total_sales_volume

        # Nominal GDP
        nominal_gdp = record["total_production"] * record["avg_goods_price"]
        record["gdp"] = nominal_gdp  # Explicitly store as 'gdp'

        if nominal_gdp > 0:
            record["labor_share"] = total_labor_income / nominal_gdp
        else:
            record["labor_share"] = 0.0

        # 2. Velocity of Money
        money_supply_m1 = total_household_assets + total_firm_assets
        if money_supply_m1 > 0:
            record["velocity_of_money"] = nominal_gdp / money_supply_m1
        else:
            record["velocity_of_money"] = 0.0

        # 3. Inventory Turnover
        if total_inventory > 0:
            record["inventory_turnover"] = total_volume / total_inventory
        else:
            record["inventory_turnover"] = 0.0

        # --- Phase 23: Opportunity Index & Education Metrics ---
        total_edu = sum(h._econ_state.education_level for h in households if h._bio_state.is_active)
        record["avg_education_level"] = total_edu / total_households if total_households > 0 else 0.0

        brain_waste = [
            h for h in households 
            if h._bio_state.is_active
            and h._econ_state.aptitude >= 0.8
            and h._econ_state.education_level < 2.0
        ]
        record["brain_waste_count"] = len(brain_waste)

        # --- TD-015: Centralized Metrics (Gini, Cohesion, Population) ---
        pop_metrics = self.calculate_population_metrics(households, markets)

        record["active_population"] = pop_metrics["active_count"]

        # Quintiles
        dist = pop_metrics["distribution"]
        record["quintile_1_avg_assets"] = dist.get("q1", 0.0)
        record["quintile_2_avg_assets"] = dist.get("q2", 0.0)
        record["quintile_3_avg_assets"] = dist.get("q3", 0.0)
        record["quintile_4_avg_assets"] = dist.get("q4", 0.0)
        record["quintile_5_avg_assets"] = dist.get("q5", 0.0)

        # Gini
        gini = self.calculate_gini_coefficient(pop_metrics["all_assets"])
        record["gini"] = gini

        # Social Cohesion
        cohesion = self.calculate_social_cohesion(households)
        record["social_cohesion"] = cohesion

        for field in self.all_fieldnames:
            record.setdefault(field, 0)

        # Store the record in metrics with bounded size to prevent OOM
        for key, value in record.items():
            if key != "time":
                # Ensure we have a list for this key
                lst = self.metrics.setdefault(key, [])
                lst.append(value)
                # Keep max 2000 points to bound memory usage
                if len(lst) > 2000:
                    lst.pop(0)

        # Update SMA Histories
        self.gdp_history.append(record.get("gdp", 0.0))
        self.cpi_history.append(record.get("goods_price_index", 0.0))
        self.m2_leak_history.append(m2_leak)

    def get_smoothed_values(self) -> Dict[str, float]:
        """
        Returns the Simple Moving Average (SMA) of key indicators.
        Window size is defined by self.history_window (default 50).
        """
        return {
            "gdp_sma": statistics.mean(self.gdp_history) if self.gdp_history else 0.0,
            "cpi_sma": statistics.mean(self.cpi_history) if self.cpi_history else 0.0,
            "m2_leak_sma": statistics.mean(self.m2_leak_history) if self.m2_leak_history else 0.0
        }

    def get_latest_indicators(self) -> Dict[str, Any]:
        """가장 최근에 기록된 경제 지표들을 딕셔너리 형태로 반환합니다."""
        latest_indicators = {}
        for key, values in self.metrics.items():
            if values:
                latest_indicators[key] = values[-1]
        return latest_indicators

    def calculate_monetary_aggregates(self, world_state: 'WorldState') -> Dict[str, float]:
        """
        TD-015: Calculates M0, M1, M2 money supply aggregates.
        Delegates to WorldState for precise Penny Standard calculation.
        """
        m0_pennies = world_state.calculate_base_money().get(DEFAULT_CURRENCY, 0)
        supply_dto = world_state.calculate_total_money()
        m2_pennies = supply_dto.total_m2_pennies
        
        return {
            "m0": float(m0_pennies) / 100.0,
            "m1": float(m2_pennies) / 100.0,
            "m2": float(m2_pennies) / 100.0
        }

    def get_m2_money_supply(self, world_state: 'WorldState') -> float:
        """
        Calculates the M2 money supply for economic reporting.
        Deprecated: Use calculate_monetary_aggregates instead.
        """
        return self.calculate_monetary_aggregates(world_state)["m2"]
