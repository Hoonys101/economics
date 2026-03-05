# Design Document: Household Engine Singleton (WO-SPEC-MEM-SINGLETON-HOUSEHOLD)

## 1. Introduction

- **Purpose**: Resolve `MemoryError` and excessive object instantiation overhead during simulation startup. By converting 8 stateless engines to class variables in `Household` and sharing `goods_info_map`, we shift the memory complexity of these components from $O(N)$ (per agent) to $O(1)$ (global).
- **Scope**: Modifications are strictly confined to `simulation/core_agents.py` (specifically `Household.__init__` and class body) and `modules/system/builders/simulation_builder.py`.

## 2. System Architecture (High-Level)

The refactoring solidifies the **Stateless Engine & Orchestrator (SEO) Pattern**. The `Household` (Orchestrator) will delegate logic to shared, stateless engines residing at the class level. This enforces purity, prevents hidden state buildup inside engines, and drastically reduces memory pressure for large-scale economies.

## 3. Detailed Design

### 3.1. Component: `Household` (`simulation/core_agents.py`)

- **Logic**: 
  1. Declare the 8 specific engines as class attributes.
  2. Remove their initialization from `__init__`.
  3. Introduce `shared_goods_info_map` parameter to prevent redundant dictionary comprehensions for each instance.
- **Pseudo-code (Changes)**:
  ```python
  from simulation.engines.lifecycle_engine import LifecycleEngine
  from simulation.engines.needs_engine import NeedsEngine
  from simulation.engines.social_engine import SocialEngine
  from simulation.engines.budget_engine import BudgetEngine
  from simulation.engines.consumption_engine import ConsumptionEngine
  from simulation.engines.belief_engine import BeliefEngine
  from simulation.engines.crisis_engine import CrisisEngine
  from simulation.engines.housing_connector import HousingConnector

  class Household(IHousehold):
      # --- Class-Level Stateless Engines (O(1) Memory) ---
      lifecycle_engine = LifecycleEngine()
      needs_engine = NeedsEngine()
      social_engine = SocialEngine()
      budget_engine = BudgetEngine()
      consumption_engine = ConsumptionEngine()
      belief_engine = BeliefEngine()
      crisis_engine = CrisisEngine()
      housing_connector = HousingConnector()

      def __init__(
          self, 
          core_config: AgentCoreConfigDTO,
          engine: Any,
          ...,
          goods_data: List[Dict[str, Any]],
          shared_goods_info_map: Optional[Dict[str, Any]] = None,
          ...
      ):
          # Legacy __init__ logic...
          
          # [DELETED]: self.lifecycle_engine = LifecycleEngine() ... (and 7 others)

          # --- Memory-Optimized Goods Mapping ---
          if shared_goods_info_map is not None:
              self.goods_info_map = shared_goods_info_map
          else:
              # Fallback for backward compatibility in legacy test setups
              self.goods_info_map = {g["id"]: g for g in goods_data} if goods_data else {}
  ```

### 3.2. Component: `SimulationBuilder` (`modules/system/builders/simulation_builder.py`)

- **Logic**: Pre-calculate the `goods_info_map` once, then pass it as a shared reference into the `Household` constructor.
- **Pseudo-code (Changes)**:
  ```python
  # In create_simulation(...) before the Household loop:
  goods_data = [
      {"id": good_name, **good_attrs}
      for good_name, good_attrs in config.GOODS.items()
  ]
  shared_goods_info_map = {g["id"]: g for g in goods_data}

  # In the Household generation loop:
  for i in range(num_households):
      # ...
      household = Household(
          core_config=core_config,
          engine=household_decision_engine,
          talent=Talent(max(0.5, random.gauss(1.0, 0.2)), {}),
          goods_data=goods_data,
          shared_goods_info_map=shared_goods_info_map, # Shared reference
          personality=personality,
          # ...
      )
  ```

## 4. Technical Considerations & Audits

### 4.1. [Debt Review] Mandatory Ledger Audit
- **Resolves**: Implements the exact remediation strategy proposed in `audit_mem_agent_bloat.md`. This directly resolves the structural technical debt of unscalable per-agent object bloat without creating new systemic debt.

### 4.2. Risk & Impact Audit (기술적 위험 분석)
- **Cross-Contamination via Mutability Risk**: While engines are designated as Stateless, any future developer improperly assigning state (`self.last_tick = tick`) inside these engines will now contaminate the entire simulation due to the class-level singleton nature. Strict code-review guidelines enforcing the SEO pattern are required.
- **Initialization Impact**: Safe. Existing parameters stay intact; added `shared_goods_info_map` has a fallback to ensure older integration tests do not break.

### 4.3. 🚨 [Conceptual Debt] (정합성 부채)
- **Firm Bloat Pending**: `Firm` agents and `DecisionEngine` managers (e.g., `ConsumptionManager`) are also known to instantiate per-agent logic wrappers (as seen in `audit_mem_agent_bloat.md`). Fixing those is out of the `WO-SPEC-MEM-SINGLETON-HOUSEHOLD` constraint scope. This conceptual inconsistency (Households optimized, Firms not) remains as planned debt for a subsequent wave.

### 4.4. 검증 계획 (Testing & Verification Strategy)
- **Unit Testing Memory Identity**:
  - Test that `id(Household.lifecycle_engine) == id(hh_instance.lifecycle_engine)`.
  - Test that `id(hh1.goods_info_map) == id(hh2.goods_info_map)`.
- **Mocking Guide for Engineers**: 
  - **CRITICAL**: Because engines are now class variables, monkeypatching an instance (`hh.needs_engine = MagicMock()`) will NOT work correctly if the logic retrieves it via the class, and mocking the class directly (`Household.needs_engine = MagicMock()`) will bleed into other tests if not torn down.
  - **Required Pattern**: Always use `mock.patch.object` to ensure context-managed cleanup:
    ```python
    with patch.object(Household, 'needs_engine') as mock_needs:
        mock_needs.process.return_value = expected_dto
        # Execute test...
    ```

## 5. Mandatory Reporting Verification
🚨 **[Action Required by Implementer]**:
Upon completion of the implementation and test verification, you MUST write an insight report detailing any friction encountered with legacy tests or engine statefulness.
- **Target File**: `communications/insights/WO-SPEC-MEM-SINGLETON-HOUSEHOLD.md`
- Do not append these findings to shared `manual.md` files. This isolated report is a hard requirement for mission completion.

---

## 6. 🔍 [ANTIGRAVITY REVIEW] 보완 사항

### Import 경로 수정
> [!WARNING]
> Section 3.1의 pseudo-code import 경로가 **할루시네이션**입니다.
> 실제 import 경로 (`core_agents.py:L35-49`):
> ```python
> from modules.household.engines.lifecycle import LifecycleEngine
> from modules.household.engines.needs import NeedsEngine
> from modules.household.engines.social import SocialEngine
> from modules.household.engines.budget import BudgetEngine
> from modules.household.engines.consumption import ConsumptionEngine
> from modules.household.engines.belief import BeliefEngine
> from modules.household.engines.crisis import CrisisEngine
> from modules.household.connectors.housing import HousingConnector
> ```
> 이 import들은 이미 파일 상단에 존재하므로 **추가 import 불필요**.

### 코드 확인 결과
- ✅ 엔진 초기화: `core_agents.py:L118-125`에서 8줄 확인
- ✅ goods_info_map: `core_agents.py:L218` 확인
- ✅ `goods_data` 파라미터: `__init__` 시그니처 L97에 존재
- ✅ 기존 엔진은 **모두 인자 없는 기본 생성자** 사용 → 클래스 변수 전환 안전