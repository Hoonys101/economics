from _typeshed import Incomplete

class VectorizedHouseholdPlanner:
    config: Incomplete
    child_monthly_cost: Incomplete
    breeding_cost_base: Incomplete
    opp_cost_factor: Incomplete
    emotional_base: Incomplete
    tech_enabled: Incomplete
    fertility_rate: Incomplete
    survival_threshold: Incomplete
    food_consumption_qty: Incomplete
    max_purchase_qty: Incomplete
    logger: Incomplete
    def __init__(self, config) -> None: ...
    def decide_breeding_batch(self, agents: list):
        """
        WO-048 Logic의 벡터화 버전
        """
    def decide_consumption_batch(self, agents: list, market_data: dict):
        """
        WO-051: Vectorized Consumption Logic
        Determines who should consume food (from inventory) and who should buy food (from market).
        """
