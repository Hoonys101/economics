# Work Order: WO-051-Engine-Optimization (Vectorization)

**Date:** 2026-01-12
**Phase:** Phase 22 (Completion)
**Assignee:** Jules (Worker AI)
**Objective:** 개별 에이전트의 반복문(`for`) 연산을 `NumPy` 기반의 행렬 연산(Batch Processing)으로 대체하여 연산 속도를 10배 이상 향상시킨다.

## 1. Architecture Refactoring (The ETL Pattern)

기존의 `Agent.decide()` 호출 방식을 폐기하고, **Extract-Compute-Inject (ETL)** 패턴을 도입합니다.

1. **Extract:** 에이전트 객체들로부터 필요한 속성(Income, Age 등)만 뽑아내어 NumPy 배열(Vector)로 변환.
2. **Compute:** 수백 명의 NPV 계산을 단 한 번의 행렬 연산으로 처리.
3. **Inject:** 계산 결과(True/False)를 다시 개별 에이전트에게 할당.

## 2. Implementation Specification

### A. New Module: `simulation/ai/vectorized_planner.py`

새로운 클래스 `VectorizedHouseholdPlanner`를 생성합니다.

```python
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
        
        children_counts = np.array([a.children_count for a in agents], dtype=np.float32)
        
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

```

### B. Integration: `simulation/engine.py`

엔진의 메인 루프에서 개별 호출을 제거하고 배치 호출로 변경합니다.

**Before (Legacy):**
*Currently found in `run_tick` method ~line 582*
```python
        # 2. Reproduction Decision
        birth_requests = []
        for household in self.households:
             if household.is_active:
                 # Check decision logic
                 context = DecisionContext(...)
                 if household.decision_engine.decide_reproduction(context):
                     birth_requests.append(household)
```

**After (Vectorized):**
1. Add import: `from simulation.ai.vectorized_planner import VectorizedHouseholdPlanner`
2. Initialize in `__init__`: `self.breeding_planner = VectorizedHouseholdPlanner(self.config_module)`
3. Replace logic in `run_tick`:

```python
        # 2. Reproduction Decision (Vectorized WO-051)
        birth_requests = []
        
        # Filter Candidates: Active, Age 20-45 (Loose filter for extraction), Female? (Design says Agents are Households, Gender is attribute)
        # Spec says "20 <= age <= 45".
        # We can pass all active households to batch planner, and let it filter by age/solvency.
        # But for efficiency, we pass active households.
        
        active_households = [h for h in self.households if h.is_active]
        if active_households:
            decisions = self.breeding_planner.decide_breeding_batch(active_households)
            
            for h, decision in zip(active_households, decisions):
                if decision:
                    birth_requests.append(h)
```

### C. Dependency Check
`numpy` is confirmed to be in `requirements.txt`.

## 3. Implementation Steps for Jules

1. **Step 1: Create Class:** `simulation/ai/vectorized_planner.py` 생성 및 위 코드 복사.
2. **Step 2: Engine Modification:** `simulation/engine.py` 수정.
   - Import 추가.
   - `__init__`에서 Planner 초기화.
   - `run_tick`에서 Loop 교체.
3. **Step 3: Verification:** 기존 테스트 `tests/test_wo048_breeding.py`가 여전히 통과하는지 확인 (로직은 동일해야 함). 혹은 간단한 성능 테스트 `tests/test_vectorization_speed.py` 작성 (Optional).

