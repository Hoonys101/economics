import numpy as np
import logging

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

        # Fertility Check: 20 <= age <= 45
        is_fertile = (ages >= 20) & (ages <= 45)

        # 3. Final Decision Mask (Boolean Array)
        # 모든 조건이 True여야 함
        decisions = (npv > 0) & is_solvent & is_fertile

        return decisions.tolist()
