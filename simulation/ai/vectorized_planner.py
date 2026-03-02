import numpy as np
import logging
from modules.system.api import DEFAULT_CURRENCY

from simulation.ai.api import IPlanner

class VectorizedHouseholdPlanner(IPlanner):
    def __init__(self, config):
        self.config = config
        # Global Caching: 반복 계산되는 상수 미리 저장
        # Handle cases where config might not have attributes if running in isolation, but assume config has them based on WO-048
        self.child_monthly_cost = getattr(config, "CHILD_MONTHLY_COST", 500.0)
        self.breeding_cost_base = self.child_monthly_cost * 12 * 20
        self.opp_cost_factor = getattr(config, "OPPORTUNITY_COST_FACTOR", 0.3) * 12 * 20
        self.emotional_base = getattr(config, "CHILD_EMOTIONAL_VALUE_BASE", 500000.0)
        self.tech_enabled = getattr(config, "TECH_CONTRACEPTION_ENABLED", True)
        self.fertility_rate = getattr(config, "BIOLOGICAL_FERTILITY_RATE", 0.15)

        # Consumption Constants
        try:
            self.survival_threshold = float(getattr(config, "SURVIVAL_NEED_CONSUMPTION_THRESHOLD", 50.0))
        except (TypeError, ValueError):
            self.survival_threshold = 50.0

        self.food_consumption_qty = getattr(config, "FOOD_CONSUMPTION_QUANTITY", 1.0)
        self.max_purchase_qty = getattr(config, "FOOD_PURCHASE_MAX_PER_TICK", 5.0)

        self.logger = logging.getLogger(__name__)

    def decide_breeding_batch(self, agents: list):
        count = len(agents)
        if count == 0: return []

        fertility = float(getattr(self, "fertility_rate", 0.15))

        if getattr(self, "tech_enabled", True) == False:
            import numpy as np
            vals = np.random.random(count)
            decisions = vals < fertility
            return decisions.tolist()

        ages = []
        wages = []
        children_counts = []

        for a in agents:
            try:
                ages.append(float(a.age))
            except (AttributeError, TypeError, ValueError): ages.append(20.0)

            try:
                v = getattr(a, "current_wage", 0.0)
                wages.append(float(v))
            except (AttributeError, TypeError, ValueError): wages.append(0.0)

            try:
                v = getattr(a, "children_ids", [])
                children_counts.append(float(len(v)) if isinstance(v, list) else 0.0)
            except (AttributeError, TypeError, ValueError): children_counts.append(0.0)

        c_monthly = float(getattr(self, "child_monthly_cost", 500.0))
        b_cost_base = float(getattr(self, "breeding_cost_base", c_monthly * 12 * 20))
        o_factor = float(getattr(self, "opp_cost_factor", 0.3 * 12 * 20))
        e_base = float(getattr(self, "emotional_base", 500000.0))

        start_age = 20.0
        end_age = 45.0
        try:
            if hasattr(self, "config") and self.config is not None:
                start_age = float(getattr(self.config, "REPRODUCTION_AGE_START", 20))
                end_age = float(getattr(self.config, "REPRODUCTION_AGE_END", 45))
        except (AttributeError, TypeError, ValueError): pass

        decisions = []
        for i in range(count):
            try:
                a = float(ages[i])
                w = float(wages[i])
                c = float(children_counts[i])

                monthly_income = w * 8.0 * 20.0
                total_cost = b_cost_base + (monthly_income * o_factor)
                total_benefit = (e_base / (c + 1.0)) + (monthly_income * 0.1 * 12.0 * 20.0)

                npv = total_benefit - total_cost
                is_solvent = monthly_income > (c_monthly * 2.5)
                is_fertile = (a >= start_age) and (a <= end_age)

                if npv > 0 and is_solvent and is_fertile:
                    decisions.append(True)
                else:
                    decisions.append(False)
            except (AttributeError, TypeError, ValueError):
                decisions.append(False)

        return decisions

    def decide_consumption_batch(self, agents: list, market_data: dict):
        count = len(agents)
        if count == 0:
            return {'consume': [], 'buy': []}

        inv_list = []
        for a in agents:
            try:
                v = a.get_quantity("basic_food")
                inv_list.append(float(v))
            except (AttributeError, TypeError, ValueError):
                inv_list.append(0.0)

        asset_list = []
        for a in agents:
            try:
                if hasattr(a.assets, 'get'):
                    v = a.assets.get("currency", 0.0)
                else:
                    v = a.assets
                asset_list.append(float(v))
            except (AttributeError, TypeError, ValueError):
                asset_list.append(0.0)

        need_list = []
        for a in agents:
            try:
                if hasattr(a.needs, 'get'):
                    v = a.needs.get("survival", 50.0)
                else:
                    v = a.needs
                need_list.append(float(v))
            except (AttributeError, TypeError, ValueError):
                need_list.append(50.0)

        goods_market = {}
        try:
            if hasattr(market_data, 'get'):
                goods_market = market_data.get("goods_market", {})
        except (AttributeError, TypeError, ValueError): pass

        food_price = 5.0
        try:
            v = goods_market.get("basic_food_current_sell_price", 5.0) if hasattr(goods_market, 'get') else 5.0
            food_price = float(v)
        except (AttributeError, TypeError, ValueError): pass
        if food_price <= 0: food_price = 5.0

        threshold = 50.0
        try:
            threshold = float(self.survival_threshold)
        except (AttributeError, TypeError, ValueError): pass

        consume_qty = float(getattr(self, "food_consumption_qty", 1.0))
        buy_qty = float(getattr(self, "max_purchase_qty", 5.0))

        consume_amounts = []
        buy_amounts = []

        for i in range(count):
            try:
                n = float(need_list[i])
                inv = float(inv_list[i])
                ast = float(asset_list[i])
                t = float(threshold)

                if n > t and inv > 0.0:
                    c = min(consume_qty, inv)
                    consume_amounts.append(c)
                else:
                    consume_amounts.append(0.0)

                if n > t and inv < 3.0 and ast >= food_price:
                    max_afford = ast / food_price if food_price > 0 else 0.0
                    b = min(buy_qty, max_afford)
                    buy_amounts.append(b)
                else:
                    buy_amounts.append(0.0)

            except Exception as e:
                consume_amounts.append(0.0)
                buy_amounts.append(0.0)

        return {
            'consume': consume_amounts,
            'buy': buy_amounts,
            'price': float(food_price)
        }

    def cleanup(self) -> None:
        """
        Clears cached references to config module to prevent mocks from persisting.
        """
        self.config = None
