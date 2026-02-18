from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging
import random
from dataclasses import replace
from simulation.models import Order
from simulation.ai.enums import Tactic, Aggressiveness
from .base_decision_engine import BaseDecisionEngine
from simulation.dtos import DecisionContext
from simulation.decisions.corporate_manager import CorporateManager
from modules.system.api import DEFAULT_CURRENCY
if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.ai.firm_ai import FirmAI
logger = logging.getLogger(__name__)

class AIDrivenFirmDecisionEngine(BaseDecisionEngine):
    """기업의 AI 기반 의사결정을 담당하는 엔진.
    AI (FirmAI) -> Aggressiveness Vector -> CorporateManager -> Orders
    """

    def __init__(self, ai_engine: FirmAI, config_module: Any, logger: Optional[logging.Logger]=None) -> None:
        """AIDrivenFirmDecisionEngine을 초기화합니다."""
        self.ai_engine = ai_engine
        self.config_module = config_module
        self.logger = logger if logger else logging.getLogger(__name__)
        self.corporate_manager = CorporateManager(config_module, self.logger)
        self.logger.info('AIDrivenFirmDecisionEngine initialized with CorporateManager.', extra={'tick': 0, 'tags': ['init']})

    def _make_decisions_internal(self, context: DecisionContext, macro_context: Optional[Any]=None) -> DecisionOutputDTO:
        """
        Main Decision Loop.
        1. AI decides Strategy (Vector).
        2. CorporateManager executes Strategy (Orders/Actions).
        """
        from simulation.dtos import DecisionOutputDTO
        firm_state = context.state
        agent_data = firm_state.agent_data
        action_vector = self.ai_engine.decide_action_vector(agent_data, context.market_data)
        orders = self.corporate_manager.realize_ceo_actions(firm_state, context, action_vector)
        self._apply_pricing_logic(orders, context, firm_state)
        return DecisionOutputDTO(orders=orders, metadata=action_vector)

    def _apply_pricing_logic(self, orders: List[Order], context: DecisionContext, firm_state: Any) -> None:
        """
        Applies Cost-Plus Fallback and Fire-Sale logic.
        """
        config = context.config
        market_snapshot = context.market_snapshot

        def calculate_unit_cost(item_id: str) -> float:
            goods_info = next((g for g in context.goods_data if g['id'] == item_id), None)
            base_cost = goods_info.get('production_cost', 10.0) if goods_info else 10.0
            prod_factor = firm_state.agent_data.get('productivity_factor', 1.0)
            if prod_factor <= 0:
                prod_factor = 1.0
            return base_cost / prod_factor
        for i, order in enumerate(orders):
            if not hasattr(order, 'item_id'):
                continue
            side = getattr(order, 'side', None) or getattr(order, 'order_type', None)
            if side in ['SELL', 'SET_PRICE']:
                is_unreliable = True
                if market_snapshot:
                    signals = getattr(market_snapshot, 'market_signals', None)
                    if isinstance(signals, dict):
                        signal = signals.get(order.item_id)
                        last_trade_tick = getattr(signal, 'last_trade_tick', None)
                        if last_trade_tick is not None:
                            staleness = context.current_time - last_trade_tick
                            max_staleness = getattr(config, 'max_price_staleness_ticks', 10)
                            if not isinstance(max_staleness, (int, float)):
                                max_staleness = 10
                            if staleness <= max_staleness:
                                is_unreliable = False
                if is_unreliable:
                    unit_cost = calculate_unit_cost(order.item_id)
                    margin = getattr(config, 'default_target_margin', 0.2)
                    if not isinstance(margin, (int, float)):
                        margin = 0.2
                    new_price = unit_cost * (1 + margin)
                    current_price = getattr(order, 'price_limit', order.price)
                    if abs(current_price - new_price) > 0.01:
                        self.logger.info(f'COST_PLUS_FALLBACK | Firm {firm_state.id} repricing {order.item_id} from {current_price:.2f} to {new_price:.2f} (Cost: {unit_cost:.2f})', extra={'tick': context.current_time, 'tags': ['pricing', 'cost_plus']})
                        orders[i] = replace(order, price_limit=new_price)
        fire_sale_orders = []
        fire_sale_asset_threshold = getattr(config, 'fire_sale_asset_threshold', 50.0)
        if not isinstance(fire_sale_asset_threshold, (int, float)):
            fire_sale_asset_threshold = 50.0
        assets_raw = firm_state.finance.balance
        assets = assets_raw
        if isinstance(assets_raw, dict):
            assets = assets_raw.get(DEFAULT_CURRENCY, 0.0)
        is_distressed = assets < fire_sale_asset_threshold
        if is_distressed:
            fire_sale_inv_threshold = getattr(config, 'fire_sale_inventory_threshold', 20.0)
            if not isinstance(fire_sale_inv_threshold, (int, float)):
                fire_sale_inv_threshold = 20.0
            fire_sale_target = getattr(config, 'fire_sale_inventory_target', 5.0)
            if not isinstance(fire_sale_target, (int, float)):
                fire_sale_target = 5.0
            for item_id, quantity in firm_state.production.inventory.items():
                if quantity > fire_sale_inv_threshold:
                    surplus = quantity - fire_sale_target
                    if surplus > 0:
                        fire_sale_price = 0.0
                        if market_snapshot:
                            signals = getattr(market_snapshot, 'market_signals', None)
                            if isinstance(signals, dict):
                                signal = signals.get(item_id)
                                best_bid = getattr(signal, 'best_bid', None)
                                if best_bid is not None:
                                    if not isinstance(best_bid, (int, float)):
                                        self.logger.debug(f'FIRE_SALE | Invalid best_bid type {type(best_bid)} for {item_id}, defaulting to 0.0', extra={'tick': context.current_time})
                                        best_bid = 0.0
                                    discount = getattr(config, 'fire_sale_discount', 0.2)
                                    if not isinstance(discount, (int, float)):
                                        discount = 0.2
                                    fire_sale_price = best_bid * (1.0 - discount)
                        if fire_sale_price <= 0:
                            unit_cost = calculate_unit_cost(item_id)
                            cost_discount = getattr(config, 'fire_sale_cost_discount', 0.5)
                            if not isinstance(cost_discount, (int, float)):
                                cost_discount = 0.5
                            fire_sale_price = unit_cost * (1.0 - cost_discount)
                        fire_sale_price = max(0.01, fire_sale_price)
                        self.logger.warning(f'FIRE_SALE | Firm {firm_state.id} dumping {surplus:.1f} of {item_id} at {fire_sale_price:.2f}', extra={'tick': context.current_time, 'tags': ['fire_sale']})
                        fire_sale_orders.append(Order(agent_id=firm_state.id, side='SELL', item_id=item_id, quantity=surplus, price_pennies=int(fire_sale_price * 100), price_limit=fire_sale_price, market_id=item_id))
        orders.extend(fire_sale_orders)