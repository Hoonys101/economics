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
        self.survival_threshold = getattr(config, "SURVIVAL_NEED_CONSUMPTION_THRESHOLD", 50.0)
        self.food_consumption_qty = getattr(config, "FOOD_CONSUMPTION_QUANTITY", 1.0)
        self.max_purchase_qty = getattr(config, "FOOD_PURCHASE_MAX_PER_TICK", 5.0)

        self.logger = logging.getLogger(__name__)

    def decide_breeding_batch(self, agents: list):
        """
        WO-048 Logic의 벡터화 버전
        """
        # 1. Extract Data (병목 지점이나 Python Loop보다 빠름)
        count = len(agents)
        if count == 0: return []

        # Step 1: Pre-Modern Check (Biological)
        if not self.tech_enabled:
            # Vectorized Random Choice
            # P(reproduction) = fertility_rate
            vals = np.random.random(count)
            decisions = vals < self.fertility_rate
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
        Determines who should consume food (from inventory) and who should buy food (from market).
        """
        count = len(agents)
        if count == 0:
            return {'consume': [], 'buy': []}

        # 1. Extract State
        # Inventory: "basic_food"
        inventories = np.array([a.inventory.get("basic_food", 0.0) for a in agents], dtype=np.float32)
        assets = np.array([a.assets.get(DEFAULT_CURRENCY, 0.0) if isinstance(a.assets, dict) else a.assets for a in agents], dtype=np.float32)
        survival_needs = np.array([a.needs.get("survival", 0.0) for a in agents], dtype=np.float32)

        # 2. Market Data
        # Get "basic_food" price
        goods_market = market_data.get("goods_market", {})
        food_price = goods_market.get("basic_food_current_sell_price", 5.0)
        if food_price <= 0: food_price = 5.0 # Fallback

        # 3. Vectorized Logic

        # A. Consumption Decision
        # Need > Threshold AND Inventory > 0
        should_consume = (survival_needs > self.survival_threshold) & (inventories > 0)
        # Quantity: 1.0 (Fixed by Config usually, simplifying to 1.0 for vector speed)
        consume_amounts = np.where(should_consume, self.food_consumption_qty, 0.0)
        # Cap by inventory
        consume_amounts = np.minimum(consume_amounts, inventories)

        # B. Purchase Decision (Survival Logic)
        # Need > Threshold AND Inventory < 3.0 (Buffer for safety)
        # AND Assets > Price
        should_buy = (survival_needs > self.survival_threshold) & (inventories < 3.0) & (assets >= food_price)

        # Buy Amount: Max Purchase Qty (5.0) or afford limit
        # Simple Logic: Buy 5.0 to restock buffer
        buy_amounts = np.where(should_buy, self.max_purchase_qty, 0.0)

        # Affordability check
        max_affordable = assets / food_price
        buy_amounts = np.minimum(buy_amounts, max_affordable)

        # Only buy integer units? Market usually allows floats but households often buy 1.0.
        # Let's keep it float.

        return {
            'consume': consume_amounts.tolist(),
            'buy': buy_amounts.tolist(),
            'price': float(food_price)
        }
