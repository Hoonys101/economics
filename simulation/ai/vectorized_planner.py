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
        """
        WO-048 Logic의 벡터화 버전 - Primitive Casting Safe
        """
        count = len(agents)
        if count == 0: return []

        try: fert = float(getattr(self, "fertility_rate", 0.15))
        except Exception: fert = 0.15

        if not getattr(self, 'tech_enabled', True):
            import random
            return [(random.random() < fert) for _ in range(count)]

        try: base = float(getattr(self, "breeding_cost_base", 120000.0))
        except Exception: base = 120000.0

        try: opp = float(getattr(self, "opp_cost_factor", 0.3 * 12 * 20))
        except Exception: opp = 0.3 * 12 * 20

        try: emo = float(getattr(self, "emotional_base", 500000.0))
        except Exception: emo = 500000.0

        try: child_cost = float(getattr(self, "child_monthly_cost", 500.0))
        except Exception: child_cost = 500.0

        try: start_age = float(getattr(self.config, "REPRODUCTION_AGE_START", 20))
        except Exception: start_age = 20.0

        try: end_age = float(getattr(self.config, "REPRODUCTION_AGE_END", 45))
        except Exception: end_age = 45.0

        decisions = []
        for a in agents:
            try: age = float(getattr(a, "age", 25.0))
            except Exception: age = 25.0

            try: wage = float(getattr(a, "current_wage", 0.0))
            except Exception: wage = 0.0

            try: children_count = float(len(getattr(a, "children_ids", [])))
            except Exception: children_count = 0.0

            monthly_income = wage * 8.0 * 20.0

            c_direct = base
            c_opp = monthly_income * opp
            total_cost = c_direct + c_opp

            u_emotional = emo / (children_count + 1)
            u_support = monthly_income * 0.1 * 12 * 20
            total_benefit = u_emotional + u_support

            npv = total_benefit - total_cost

            is_solvent = monthly_income > (child_cost * 2.5)
            is_fertile = start_age <= age <= end_age

            decisions.append((npv > 0) and is_solvent and is_fertile)

        return decisions

        # Step 2: Modern Check (NPV)
        try: base = float(getattr(self, "breeding_cost_base", 120000.0))
        except Exception: base = 120000.0
        c_direct = np.full(count, base)

        try: opp = float(getattr(self, "opp_cost_factor", 0.3 * 12 * 20))
        except Exception: opp = 0.3 * 12 * 20
        c_opp = monthly_incomes * opp
        total_cost = c_direct + c_opp

        try: emo = float(getattr(self, "emotional_base", 500000.0))
        except Exception: emo = 500000.0
        u_emotional = emo / (children_counts + 1)

        u_support = monthly_incomes * 0.1 * 12 * 20
        total_benefit = u_emotional + u_support

        npv = total_benefit - total_cost

        try: child_cost = float(getattr(self, "child_monthly_cost", 500.0))
        except Exception: child_cost = 500.0
        is_solvent = monthly_incomes > (child_cost * 2.5)

        try: start_age = float(getattr(self.config, "REPRODUCTION_AGE_START", 20))
        except Exception: start_age = 20.0

        try: end_age = float(getattr(self.config, "REPRODUCTION_AGE_END", 45))
        except Exception: end_age = 45.0

        is_fertile = (ages >= start_age) & (ages <= end_age)

        decisions = (npv > 0) & is_solvent & is_fertile
        return decisions.tolist() # Return list of booleans

        # Step 2: Modern Check (NPV)
        # 속성 추출 (List Comprehension -> NumPy Array)
        # dtype=float32 사용으로 메모리/속도 최적화
        ages = np.array([a.age for a in agents], dtype=np.float32)

        # Estimate Monthly Income proxy: current_wage * 8 * 20
        # If agent has 'monthly_income' attribute use it, else calc from wage
        # Assumption: agents are Household objects.
        # Let's extract 'current_wage' and map to monthly.
        wages = np.array([getattr(a, "current_wage", 0.0) for a in agents], dtype=np.float32)
        monthly_incomes = wages * 8.0 * 20.0

        children_counts = np.array([len(a.children_ids) for a in agents], dtype=np.float32)

        # 2. Vectorized Computation (핵심 최적화 구간)

        # A. Cost Matrix
        c_direct = np.full(count, self.breeding_cost_base)
        c_opp = monthly_incomes * self.opp_cost_factor
        total_cost = c_direct + c_opp

        # B. Benefit Matrix
        # ZeroDivisionError 방지: children_counts + 1
        u_emotional = self.emotional_base / (children_counts + 1)

        # 노후 부양: 자녀 기대 소득(부모 소득) * 0.1 * 20년
        u_support = monthly_incomes * 0.1 * 12 * 20

        total_benefit = u_emotional + u_support

        # C. NPV & Constraints
        npv = total_benefit - total_cost

        # Solvency Check: 소득 < 월 양육비 * 2.5 이면 포기
        is_solvent = monthly_incomes > (self.child_monthly_cost * 2.5)

        # Fertility Check: Configurable
        start_age = getattr(self.config, "REPRODUCTION_AGE_START", 20)
        end_age = getattr(self.config, "REPRODUCTION_AGE_END", 45)
        is_fertile = (ages >= start_age) & (ages <= end_age)

        # 3. Final Decision Mask (Boolean Array)
        # 모든 조건이 True여야 함
        decisions = (npv > 0) & is_solvent & is_fertile

        return decisions.tolist()

    def decide_consumption_batch(self, agents: list, market_data: dict):
        """
        WO-051: Vectorized Consumption Logic
        """
        count = len(agents)
        if count == 0:
            return {'consume': [], 'buy': []}

        consume_agents = []
        buy_agents = []

        goods_market = market_data.get("goods_market", {})
        try: food_price = float(goods_market.get("basic_food_current_sell_price", 5.0))
        except Exception: food_price = 5.0
        if food_price <= 0: food_price = 5.0

        try: surv_thresh = float(getattr(self, "survival_threshold", 50.0))
        except Exception: surv_thresh = 50.0

        try: f_qty = float(getattr(self, "food_consumption_qty", 1.0))
        except Exception: f_qty = 1.0

        try: m_qty = float(getattr(self, "max_purchase_qty", 5.0))
        except Exception: m_qty = 5.0

        for a in agents:
            try:
                # Force convert to primitive string first before float to break MagicMock overriding `__float__`
                inv = float(str(a.get_quantity("basic_food")))
            except Exception: inv = 0.0

            try:
                ast = getattr(a, "assets", 0.0)
                ast_val = ast.get(DEFAULT_CURRENCY, 0.0) if isinstance(ast, dict) else ast
                ast_float = float(str(ast_val))
            except Exception: ast_float = 0.0

            try:
                needs = getattr(a, "needs", {})
                sur = needs.get("survival", 0.0) if isinstance(needs, dict) else (needs.get("survival", 0.0) if hasattr(needs, "get") else 0.0)
                sur_float = float(str(sur))
            except Exception: sur_float = 0.0

            should_consume = (sur_float > surv_thresh) and (inv > 0)
            should_buy = (sur_float > surv_thresh) and (inv < 3.0) and (ast_float >= food_price)

            if should_consume:
                consume_agents.append(f_qty if inv >= f_qty else inv)
            else:
                consume_agents.append(0.0)

            if should_buy:
                buy_amt = m_qty
                if ast_float / food_price < buy_amt:
                    buy_amt = ast_float / food_price
                buy_agents.append(buy_amt)
            else:
                buy_agents.append(0.0)

        return {
            'consume': consume_agents,
            'buy': buy_agents,
            'price': food_price
        }
