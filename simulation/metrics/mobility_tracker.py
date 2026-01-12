import numpy as np
from typing import Dict

class MobilityRecord:
    def __init__(self, parent_id: int, child_id: int, parent_wealth_at_birth: float):
        self.parent_id = parent_id
        self.child_id = child_id
        self.parent_wealth = parent_wealth_at_birth
        self.child_wealth = 0.0
        self.is_complete = False

class MobilityTracker:
    def __init__(self):
        self.records: Dict[int, MobilityRecord] = {} # Key: child_id

    def register_birth(self, parent_id: int, child_id: int, parent_wealth: float):
        """자녀 출생 시 부모의 현재 자산을 기록합니다."""
        self.records[child_id] = MobilityRecord(parent_id, child_id, parent_wealth)

    def record_final_wealth(self, child_id: int, wealth: float):
        """자녀 사망 시 또는 시뮬레이션 종료 시 자녀의 최종 자산을 기록합니다."""
        if child_id in self.records:
            self.records[child_id].child_wealth = wealth
            self.records[child_id].is_complete = True

    def calculate_ige(self) -> float:
        """
        IGE (Intergenerational Income Elasticity) 계산.
        산식: log(Child_Wealth + 1) = alpha + Beta * log(Parent_Wealth + 1)
        Beta (IGE) = Cov(log_p, log_c) / Var(log_p)
        """
        valid_data = [
            (np.log(r.parent_wealth + 1), np.log(r.child_wealth + 1))
            for r in self.records.values() if r.is_complete and r.parent_wealth > 0
        ]

        if len(valid_data) < 2:
            return 0.0

        x, y = zip(*valid_data)
        # np.cov returns covariance matrix
        # [[Var(x), Cov(x,y)], [Cov(y,x), Var(y)]]
        covariance = np.cov(x, y)[0, 1]
        variance = np.var(x)

        if variance == 0:
            return 0.0

        return float(covariance / variance)

    def calculate_r_squared(self) -> float:
        """
        Calculate R-squared (Coefficient of Determination) for the log-log regression.
        R^2 = (Cov(X, Y) / (Std(X) * Std(Y)))^2
        """
        valid_data = [
            (np.log(r.parent_wealth + 1), np.log(r.child_wealth + 1))
            for r in self.records.values() if r.is_complete and r.parent_wealth > 0
        ]

        if len(valid_data) < 2:
            return 0.0

        x, y = zip(*valid_data)

        # Pearson correlation coefficient
        corr_matrix = np.corrcoef(x, y)
        correlation = corr_matrix[0, 1]

        return float(correlation ** 2)
