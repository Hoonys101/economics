from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional
import logging

from simulation.models import Order
from simulation.decisions.base_decision_engine import BaseDecisionEngine
# import config # Removed direct import
if TYPE_CHECKING:
    from simulation.firms import Firm

logger = logging.getLogger(__name__)

class FirmDecisionEngine(BaseDecisionEngine):
    """기업의 의사결정 로직을 담당하는 엔진.

    생산 목표 조정, 노동 수요 결정, 재화 판매 주문 생성 등 기업의 핵심 의사결정을 수행합니다.
    """
    def __init__(self, ai_engine: Any, config_module: Any, goods_market: Any = None, labor_market: Any = None, loan_market: Any = None, logger: Optional[logging.Logger] = None) -> None:
        """FirmDecisionEngine을 초기화합니다.

        Args:
            config_module: 시뮬레이션 설정을 담고 있는 모듈 (기본값: config).
            goods_market: 상품 시장 인스턴스.
            labor_market: 노동 시장 인스턴스.
            loan_market: 대출 시장 인스턴스.
            logger (logging.Logger, optional): 로깅을 위한 Logger 인스턴스. 기본값은 None.
        """
        super().__init__() # BaseDecisionEngine의 __init__은 인자를 받지 않습니다.
        self.ai_engine = ai_engine # Store the AI engine
        self.config_module = config_module
        self.goods_market = goods_market
        self.labor_market = labor_market
        self.loan_market = loan_market # LoanMarket 추가
        self.logger = logger if logger else logging.getLogger(__name__)
        self.logger.info("FirmDecisionEngine initialized.", extra={'tick': 0, 'tags': ['init']})

    def _calculate_dynamic_wage_offer(self, firm: Firm) -> float:
        """기업의 수익성 이력을 바탕으로 동적인 임금 제시액을 계산합니다."""
        if not firm.profit_history:
            return self.config_module.BASE_WAGE

        # 1. 평균 수익 계산
        avg_profit = sum(firm.profit_history) / len(firm.profit_history)

        # 2. 수익 기반 프리미엄 계산
        # 단순화를 위해 평균 수익을 직접 사용하여 프리미엄 계산
        # (예: BASE_WAGE의 10배를 기준으로 정규화)
        profit_based_premium = avg_profit / (self.config_module.BASE_WAGE * 10.0) 
        
        # 3. 최종 프리미엄 계산 (민감도 및 최대치 적용)
        wage_premium = max(0, min(profit_based_premium * self.config_module.WAGE_PROFIT_SENSITIVITY, self.config_module.MAX_WAGE_PREMIUM))
        
        # 4. 최종 임금 제시액 반환
        return self.config_module.BASE_WAGE * (1 + wage_premium)

    def make_decisions(self, firm: Firm, current_tick: int, market_data: Dict[str, Any]) -> List[Order]:
        """기업의 현재 상태와 시장 데이터를 바탕으로 의사결정을 수행하고 주문 리스트를 반환합니다.

        주요 의사결정:
        1.  **생산 목표 조정**: 재고 수준에 따라 생산 목표를 증감합니다.
        2.  **노동 수요 결정**: 생산 목표 달성에 필요한 노동력을 계산하고 고용 주문을 생성합니다.
        3.  **재화 판매 주문**: 재고 수준과 시장 상황을 고려하여 재화 판매 주문을 생성합니다.

        Args:
            firm (Firm): 의사결정을 수행할 기업 에이전트 인스턴스.
            current_tick (int): 현재 시뮬레이션 틱.
            market_data (Dict[str, Any]): 현재 시장 상태를 포함하는 딕셔너리.

        Returns:
            List[Order]: 생성된 주문(Order) 객체들의 리스트.
        """
        self.logger.info(f"Firm {firm.id} starting make_decisions. Current Employees: {len(firm.employees)}", extra={'tick': current_tick, 'agent_id': firm.id, 'tags': ['decision_start']})
        all_orders: List[Order] = [] 
        
        # 1. 생산 목표 조정 (재고 수준에 따라)
        item_id = firm.specialization
        current_inventory = firm.inventory.get(item_id, 0)
        target_quantity = firm.production_target

        if current_inventory > target_quantity * self.config_module.OVERSTOCK_THRESHOLD:
            # 과잉 재고: 생산 목표 감소
            firm.production_target = max(self.config_module.FIRM_MIN_PRODUCTION_TARGET, target_quantity * (1 - self.config_module.PRODUCTION_ADJUSTMENT_FACTOR))
            self.logger.info(f"Overstock of {item_id}. Reducing production target to {firm.production_target:.1f}", extra={'tick': current_tick, 'agent_id': firm.id, 'tags': ['production_target']})
        elif current_inventory < target_quantity * self.config_module.UNDERSTOCK_THRESHOLD:
            # 재고 부족: 생산 목표 증가
            firm.production_target = min(self.config_module.FIRM_MAX_PRODUCTION_TARGET, target_quantity * (1 + self.config_module.PRODUCTION_ADJUSTMENT_FACTOR))
            self.logger.info(f"Understock of {item_id}. Increasing production target to {firm.production_target:.1f}", extra={'tick': current_tick, 'agent_id': firm.id, 'tags': ['production_target']})

        # 2. 노동 수요 결정 (조정된 생산 목표에 따라)
        total_needed_labor = 0
        item_id = firm.specialization
        target_quantity = firm.production_target
        current_inventory = firm.inventory.get(item_id, 0)
        # 목표 재고량과 현재 재고의 차이만큼 생산 필요
        needed_production = max(0, target_quantity - current_inventory)
        # 생산성 계수를 고려하여 필요한 노동력 계산
        needed_labor_for_item = needed_production / firm.productivity_factor
        total_needed_labor += needed_labor_for_item
        self.logger.debug(f"FIRM_DECISION | Firm {firm.id} - Total Needed Labor: {total_needed_labor:.2f}, Current Employees: {len(firm.employees)}", extra={'tick': current_tick, 'agent_id': firm.id, 'tags': ['labor_debug']})
        
        # 5. 현재 고용된 직원 수와 필요한 노동력을 비교하여 고용 결정
        # 이전 틱의 평균 임금을 기준으로 임금 설정
        base_offer = market_data.get('avg_wage', self.config_module.BASE_WAGE)
        
        # 고용 실패에 따른 경쟁적 임금 프리미엄
        competitive_premium = 0.0
        if current_tick > 1 and total_needed_labor > len(firm.employees) and firm.hires_last_tick == 0:
            # 프리미엄을 이전 평균 임금의 일정 비율로 설정하여 시장 상황에 맞게 스케일링
            competitive_premium = base_offer * self.config_module.WAGE_COMPETITION_PREMIUM
            self.logger.info(f"Failed to hire last tick. Adding competitive premium of {competitive_premium:.2f}", extra={'tick': current_tick, 'agent_id': firm.id, 'tags': ['wage_premium']})

        # 자산 기반 프리미엄

        
        # 최종 제안 임금
        offered_wage = self._calculate_dynamic_wage_offer(firm)
        self.logger.debug(f"FIRM_DECISION | Firm {firm.id} - Offered Wage: {offered_wage:.2f}", extra={'tick': current_tick, 'agent_id': firm.id, 'tags': ['labor_debug']})

        if len(firm.employees) < self.config_module.FIRM_MIN_EMPLOYEES:
            order = Order(firm.id, 'BUY', 'labor', 1.0, offered_wage, 'labor_market')
            all_orders.append(order)
            self.logger.info(f"Hiring to meet minimum employee count. Offering dynamic wage: {offered_wage:.2f}", extra={'tick': current_tick, 'agent_id': firm.id, 'tags': ['hiring', 'dynamic_wage']})
        elif total_needed_labor > len(firm.employees) and len(firm.employees) < self.config_module.FIRM_MAX_EMPLOYEES:
            order = Order(firm.id, 'BUY', 'labor', 1.0, offered_wage, 'labor_market')
            all_orders.append(order)
            self.logger.info(f"Planning to BUY labor for dynamic wage {offered_wage:.2f}", extra={'tick': current_tick, 'agent_id': firm.id, 'tags': ['hiring', 'dynamic_wage']})
        
        # 6. 재화 판매 주문 (재고 수준에 따른 가격 조정)
        item_id = firm.specialization
        current_inventory = firm.inventory.get(item_id, 0)
        
        if current_inventory > 0:
            target_inventory = firm.production_target
            base_price = firm.last_prices.get(item_id, self.config_module.GOODS_MARKET_SELL_PRICE)
            adjusted_price = base_price
            if target_inventory > 0:
                diff_ratio = (current_inventory - target_inventory) / target_inventory
                signed_power = (abs(diff_ratio) ** self.config_module.PRICE_ADJUSTMENT_EXPONENT)
                if diff_ratio < 0: 
                    adjusted_price = base_price * (1 + signed_power * self.config_module.PRICE_ADJUSTMENT_FACTOR) # More aggressive price increase
                else: 
                    adjusted_price = base_price * (1 - signed_power * self.config_module.PRICE_ADJUSTMENT_FACTOR)
            
            final_price = max(self.config_module.MIN_SELL_PRICE, min(self.config_module.MAX_SELL_PRICE, adjusted_price))
            self.logger.debug(f"FIRM_PRICE_CALC | Firm {firm.id} Item {item_id}: Inv={current_inventory:.1f}, Tgt={target_inventory:.1f}, BaseP={base_price:.2f}, FinalP={final_price:.2f}", extra={'tick': current_tick, 'agent_id': firm.id, 'tags': ['price_calc']})
            firm.last_prices[item_id] = final_price

            quantity_to_sell = min(current_inventory, self.config_module.MAX_SELL_QUANTITY)
            if quantity_to_sell > 0:
                order = Order(firm.id, 'SELL', item_id, quantity_to_sell, final_price, 'goods_market')
                all_orders.append(order)
                self.logger.info(f"Planning to SELL {quantity_to_sell:.1f} of {item_id} at price {final_price:.2f}", extra={'tick': current_tick, 'agent_id': firm.id, 'tags': ['sell_order']})

        return all_orders