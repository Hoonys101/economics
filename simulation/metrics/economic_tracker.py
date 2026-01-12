from __future__ import annotations
from typing import List, Dict, Any
import logging

from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.core_markets import Market

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
            "total_labor_income": [],
            "total_sales_volume": [],
        }
        self.config_module = config_module  # Store config_module
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
        ]
        self.logger = logging.getLogger(__name__)

    def track(
        self,
        time: int,
        households: List[Household],
        firms: List[Firm],
        markets: Dict[str, Market],
        money_supply: float = 0.0,
    ) -> None:
        """현재 시뮬레이션 틱의 경제 지표를 계산하고 기록합니다."""
        self.logger.debug(
            f"TRACKER_UPDATE | Starting tracker update for tick {time}",
            extra={"tick": time, "tags": ["tracker"]},
        )
        record: Dict[str, Any] = {"time": time}

        # WO-043: Track Money Supply
        record["money_supply"] = money_supply

        # Perform calculations...
        total_household_assets = sum(
            h.assets for h in households if getattr(h, "is_active", True)
        )
        total_firm_assets = sum(
            f.assets for f in firms if getattr(f, "is_active", False)
        )
        record["total_household_assets"] = total_household_assets
        record["total_firm_assets"] = total_firm_assets

        total_households = len([h for h in households if getattr(h, "is_active", True)])
        unemployed_households = len(
            [
                h
                for h in households
                if getattr(h, "is_active", True) and not h.is_employed
            ]
        )
        record["unemployment_rate"] = (
            (unemployed_households / total_households) * 100
            if total_households > 0
            else 0
        )

        # Simplified logic for market data - assumes market objects have this data
        # Calculate weighted average price for goods and find food market data
        total_volume = 0.0
        weighted_price_sum = 0.0

        # Track specific food metrics (assuming 'basic_food' is the primary food or iterating)
        food_price_sum = 0.0
        food_volume_sum = 0.0

        # We can also look for "food" or "basic_food" specifically
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

                # Check if this is a food item
                if "food" in market_id:
                    if volume > 0:
                         food_price_sum += avg_price * volume
                         food_volume_sum += volume
                    elif avg_price > 0:
                         # If no volume but has price (e.g. from asks), just track price?
                         # For weighted avg, we need volume. If 0 volume, we can't weight it.
                         pass

        if food_volume_sum > 0:
            record["food_avg_price"] = food_price_sum / food_volume_sum
        else:
            # Fallback to checking best asks if no trades
            # For simplicity, just use 0.0 or try to get from specific market
            f_market = markets.get(primary_food_key)
            if f_market and hasattr(f_market, "get_daily_avg_price"):
                 record["food_avg_price"] = f_market.get_daily_avg_price() or 0.0
            else:
                 record["food_avg_price"] = 0.0

        record["food_trade_volume"] = food_volume_sum

        if total_volume > 0:
            record["avg_goods_price"] = weighted_price_sum / total_volume
        else:
            record["avg_goods_price"] = 0.0

        # ... other metric calculations ...
        total_production = sum(
            f.current_production
            for f in firms
            if getattr(f, "is_active", False)
        )
        record["total_production"] = total_production

        total_consumption = sum(
            h.current_consumption for h in households if getattr(h, "is_active", True)
        )
        record["total_consumption"] = total_consumption

        total_food_consumption = sum(
            h.current_food_consumption
            for h in households
            if isinstance(h, Household) and getattr(h, "is_active", True)
        )
        record["total_food_consumption"] = total_food_consumption

        total_inventory = sum(
            sum(f.inventory.values()) for f in firms if getattr(f, "is_active", False)
        )
        record["total_inventory"] = total_inventory

        # Calculate average survival need for active households
        active_households_count = 0
        total_survival_need = 0.0
        for h in households:
            if getattr(h, "is_active", True):
                active_households_count += 1
                total_survival_need += h.needs.get("survival", 0.0)

        record["avg_survival_need"] = (
            total_survival_need / active_households_count
            if active_households_count > 0 else 0.0
        )

        # --- WO-043: Comprehensive Metrics ---
        # 1. Labor Share = Total Labor Income / Nominal GDP
        total_labor_income = sum(
            getattr(h, "labor_income_this_tick", 0.0)
            for h in households
            if getattr(h, "is_active", True)
        )
        record["total_labor_income"] = total_labor_income

        # Track Sales Volume from firms
        total_sales_volume = sum(
            getattr(f, "sales_volume_this_tick", 0.0) for f in firms
        )
        record["total_sales_volume"] = total_sales_volume

        # Nominal GDP = Total Production * Avg Goods Price
        nominal_gdp = record["total_production"] * record["avg_goods_price"]

        if nominal_gdp > 0:
            record["labor_share"] = total_labor_income / nominal_gdp
        else:
            record["labor_share"] = 0.0

        # 2. Velocity of Money = Nominal GDP / Money Supply (M1)
        # M1 = Household Assets + Firm Assets (excluding Bank/Govt)
        money_supply_m1 = total_household_assets + total_firm_assets
        record["money_supply"] = money_supply_m1

        if money_supply_m1 > 0:
            record["velocity_of_money"] = nominal_gdp / money_supply_m1
        else:
            record["velocity_of_money"] = 0.0

        # 3. Inventory Turnover = Sales Volume (Goods) / Total Inventory
        if total_inventory > 0:
            record["inventory_turnover"] = total_volume / total_inventory
        else:
            record["inventory_turnover"] = 0.0

        # --- Phase 23: Opportunity Index & Education Metrics ---
        # 1. Average Education Level
        total_edu = sum(getattr(h, "education_level", 0.0) for h in households if getattr(h, "is_active", True))
        record["avg_education_level"] = total_edu / total_households if total_households > 0 else 0.0

        # 2. Brain Waste Count (Aptitude >= 0.8 but Education < Level 2)
        brain_waste = [
            h for h in households 
            if getattr(h, "is_active", True) 
            and getattr(h, "aptitude", 0.0) >= 0.8 
            and getattr(h, "education_level", 0.0) < 2.0
        ]
        record["brain_waste_count"] = len(brain_waste)

        # 3. Government Education Spending (from direct state)
        # Note: This relies on Simulation passing the spent amount or Government state being visible.
        # However, track() doesn't receive Government instance directly. 
        # But we can assume it will be added to record via engine integration or by passing govt.


        for field in self.all_fieldnames:
            record.setdefault(field, 0.0)

        # Store the record in metrics
        for key, value in record.items():
            if key != "time":
                self.metrics.setdefault(key, []).append(value)

    def get_latest_indicators(self) -> Dict[str, Any]:
        """가장 최근에 기록된 경제 지표들을 딕셔너리 형태로 반환합니다."""
        latest_indicators = {}
        for key, values in self.metrics.items():
            if values:
                latest_indicators[key] = values[-1]
        return latest_indicators
