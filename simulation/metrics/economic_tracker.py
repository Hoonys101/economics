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
        ]
        self.logger = logging.getLogger(__name__)

    def track(
        self,
        time: int,
        households: List[Household],
        firms: List[Firm],
        markets: Dict[str, Market],
    ) -> None:
        """현재 시뮬레이션 틱의 경제 지표를 계산하고 기록합니다."""
        self.logger.debug(
            f"TRACKER_UPDATE | Starting tracker update for tick {time}",
            extra={"tick": time, "tags": ["tracker"]},
        )
        record: Dict[str, Any] = {"time": time}

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
        food_market = markets.get("food")
        if food_market and hasattr(food_market, "get_daily_avg_price"):
            record["food_avg_price"] = food_market.get_daily_avg_price()
            record["food_trade_volume"] = food_market.get_daily_volume()
        else:
            record["food_avg_price"] = 0.0
            record["food_trade_volume"] = 0.0

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
