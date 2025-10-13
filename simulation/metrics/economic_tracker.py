from __future__ import annotations
from typing import List, Dict, Any
import logging

from simulation.models import Transaction
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
        self.metrics: Dict[str, List[float]] = {"goods_price_index": [], "unemployment_rate": [], "avg_wage": []}
        self.config_module = config_module # Store config_module
        self.all_fieldnames: List[str] = [ # Keep for record structure, but not for CSV writing
            'time', 'total_household_assets', 'total_firm_assets', 'unemployment_rate',
            'food_avg_price', 'food_trade_volume', 'avg_goods_price', 'avg_wage',
            'total_production', 'total_consumption', 'total_food_consumption', 'total_inventory'
        ]
        self.logger = logging.getLogger(__name__)

    def update(self, markets: Dict[str, Market], households: List[Household], firms: List[Firm], time: int, all_transactions: List[Transaction]) -> None:
        """현재 시뮬레이션 틱의 경제 지표를 계산하고 기록합니다.

        Args:
            markets (Dict[str, Market]): 현재 시뮬레이션의 모든 시장 인스턴스.
            households (List[Household)): 현재 시뮬레이션의 모든 가계 에이전트.
            firms (List[Firm]): 현재 시뮬레이션의 모든 기업 에이전트.
            time (int): 현재 시뮬레이션 틱.
            all_transactions (List[Transaction]): 현재 틱에서 발생한 모든 거래 내역.
        """
        self.logger.info(f"Starting tracker update for tick {time}", extra={'tick': time, 'tags': ['tracker']})
        record = {}
        record["time"] = time

        total_household_assets = sum(h.assets for h in households if getattr(h, 'is_active', True))
        total_firm_assets = sum(f.assets for f in firms if getattr(f, 'is_active', False))
        record["total_household_assets"] = total_household_assets
        record["total_firm_assets"] = total_firm_assets

        total_households = len([h for h in households if getattr(h, 'is_active', True)])
        unemployed_households = len([h for h in households if getattr(h, 'is_active', True) and not h.is_employed])
        unemployment_rate = (unemployed_households / total_households) * 100 if total_households > 0 else 0
        record["unemployment_rate"] = unemployment_rate

        food_transactions = [tx for tx in all_transactions if tx.item_id == 'food' and tx.transaction_type == 'goods']
        if food_transactions:
            record["food_avg_price"] = sum(tx.price for tx in food_transactions) / len(food_transactions)
            record["food_trade_volume"] = sum(tx.quantity for tx in food_transactions)
        else:
            record["food_avg_price"] = 0.0
            record["food_trade_volume"] = 0.0

        goods_transactions = [tx for tx in all_transactions if tx.transaction_type == 'goods']
        if goods_transactions:
            avg_goods_price = sum(tx.price for tx in goods_transactions) / len(goods_transactions)
            record["avg_goods_price"] = avg_goods_price
        else:
            # If no goods transactions, carry over the last recorded avg_goods_price
            # or use a default if no history exists.
            # Now, we will store the current avg_goods_price in the tracker itself
            record["avg_goods_price"] = self.metrics.get("avg_goods_price", [self.config_module.GOODS_MARKET_SELL_PRICE])[-1] if self.metrics.get("avg_goods_price") else self.config_module.GOODS_MARKET_SELL_PRICE
        
        labor_transactions = [tx for tx in all_transactions if tx.transaction_type == 'labor']
        if labor_transactions:
            avg_wage = sum(tx.price for tx in labor_transactions) / len(labor_transactions)
            record["avg_wage"] = avg_wage
        else:
            # If no labor transactions, carry over the last recorded avg_wage
            # Now, we will store the current avg_wage in the tracker itself
            record["avg_wage"] = self.metrics.get("avg_wage", [self.config_module.BASE_WAGE])[-1] if self.metrics.get("avg_wage") else self.config_module.BASE_WAGE

        total_production = sum(f.current_production for f in firms if getattr(f, 'is_active', False))
        record["total_production"] = total_production

        total_consumption = sum(h.current_consumption for h in households if getattr(h, 'is_active', True))
        record["total_consumption"] = total_consumption

        total_food_consumption = sum(h.current_food_consumption for h in households if isinstance(h, Household) and getattr(h, 'is_active', True))
        record["total_food_consumption"] = total_food_consumption

        total_inventory = sum(sum(f.inventory.values()) for f in firms if getattr(f, 'is_active', False))
        record["total_inventory"] = total_inventory

        for field in self.all_fieldnames:
            record.setdefault(field, 0.0)

        # Store the record in metrics for later retrieval by _prepare_market_data
        for key, value in record.items():
            if key != "time": # 'time' is not a metric to be appended to a list
                self.metrics.setdefault(key, []).append(value)
