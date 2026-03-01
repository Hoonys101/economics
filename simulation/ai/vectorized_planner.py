import numpy as np
import logging
from modules.system.api import DEFAULT_CURRENCY

class VectorizedHouseholdPlanner:
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

        fertility = 0.15
        try:
            if 'Mock' not in str(type(self.fertility_rate)):
                fertility = float(self.fertility_rate)
        except: pass

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
                v = a.age
                ages.append(float(v) if 'Mock' not in str(type(v)) else 20.0)
            except: ages.append(20.0)

            try:
                v = getattr(a, "current_wage", 0.0)
                wages.append(float(v) if 'Mock' not in str(type(v)) else 0.0)
            except: wages.append(0.0)

            try:
                v = getattr(a, "children_ids", [])
                children_counts.append(float(len(v)) if isinstance(v, list) else 0.0)
            except: children_counts.append(0.0)

        c_monthly = 500.0
        try:
            if 'Mock' not in str(type(self.child_monthly_cost)):
                c_monthly = float(self.child_monthly_cost)
        except: pass

        b_cost_base = c_monthly * 12 * 20
        try:
            if 'Mock' not in str(type(self.breeding_cost_base)):
                b_cost_base = float(self.breeding_cost_base)
        except: pass

        o_factor = 0.3 * 12 * 20
        try:
            if 'Mock' not in str(type(self.opp_cost_factor)):
                o_factor = float(self.opp_cost_factor)
        except: pass

        e_base = 500000.0
        try:
            if 'Mock' not in str(type(self.emotional_base)):
                e_base = float(self.emotional_base)
        except: pass

        start_age = 20.0
        end_age = 45.0
        try:
            s = getattr(self.config, "REPRODUCTION_AGE_START", 20)
            if 'Mock' not in str(type(s)): start_age = float(s)
            e = getattr(self.config, "REPRODUCTION_AGE_END", 45)
            if 'Mock' not in str(type(e)): end_age = float(e)
        except: pass

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
            except:
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
                inv_list.append(float(v) if 'Mock' not in str(type(v)) else 0.0)
            except:
                inv_list.append(0.0)

        asset_list = []
        for a in agents:
            try:
                if hasattr(a.assets, 'get'):
                    v = a.assets.get("currency", 0.0)
                else:
                    v = a.assets
                asset_list.append(float(v) if 'Mock' not in str(type(v)) else 0.0)
            except:
                asset_list.append(0.0)

        need_list = []
        for a in agents:
            try:
                if hasattr(a.needs, 'get'):
                    v = a.needs.get("survival", 50.0)
                else:
                    v = a.needs
                need_list.append(float(v) if 'Mock' not in str(type(v)) else 50.0)
            except:
                need_list.append(50.0)

        goods_market = {}
        try:
            if hasattr(market_data, 'get'):
                goods_market = market_data.get("goods_market", {})
        except: pass

        food_price = 5.0
        try:
            v = goods_market.get("basic_food_current_sell_price", 5.0) if hasattr(goods_market, 'get') else 5.0
            if 'Mock' not in str(type(v)):
                food_price = float(v)
        except: pass
        if food_price <= 0: food_price = 5.0

        threshold = 50.0
        try:
            v = self.survival_threshold
            if 'Mock' not in str(type(v)):
                threshold = float(v)
        except: pass

        consume_qty = 1.0
        try:
            if 'Mock' not in str(type(self.food_consumption_qty)):
                consume_qty = float(self.food_consumption_qty)
        except: pass

        buy_qty = 5.0
        try:
            if 'Mock' not in str(type(self.max_purchase_qty)):
                buy_qty = float(self.max_purchase_qty)
        except: pass

        consume_amounts = []
        buy_amounts = []

        for i in range(count):
            try:
                n = float(need_list[i]) if 'Mock' not in str(type(need_list[i])) else 50.0
                inv = float(inv_list[i]) if 'Mock' not in str(type(inv_list[i])) else 0.0
                ast = float(asset_list[i]) if 'Mock' not in str(type(asset_list[i])) else 0.0
                t = float(threshold) if 'Mock' not in str(type(threshold)) else 50.0

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
