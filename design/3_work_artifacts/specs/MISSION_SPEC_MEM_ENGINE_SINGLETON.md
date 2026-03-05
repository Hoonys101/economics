# MISSION_SPEC: Engine Singleton Enforcement & Shared Data

**Mission Key**: WO-SPEC-MEM-FIX-ENGINE-SINGLETON
**Target Phase**: Memory Optimization & Refactoring

## 1. 개요 (Overview)
Agent-Level Memory Bloat (OOM) 문제를 해결하기 위해 에이전트 초기화 시 인스턴스별로 중복 생성되던 Stateless 엔진(Engine)과 매니저(Manager) 객체들을 클래스 변수(Class Attributes) 기반의 싱글톤으로 전환합니다. 더불어, 모든 에이전트가 동일하게 가지는 `goods_info_map` 등의 메타데이터를 개별 복사하는 대신 공유 참조(Shared Reference)로 변경하여 객체 생성 오버헤드와 메모리 점유를 최적화합니다. `Firm` 에이전트의 구조도 동일하게 적용됩니다.

---

## 2. 파일별 변경 사항 및 로직 해체 (Pseudo-code & Logic Steps)

### A. `simulation/core_agents.py` (Household)
**문제점**: `Household.__init__`에서 8개의 엔진을 `self` 인스턴스 변수로 매번 생성. `goods_info_map`을 리스트 기반 컴프리헨션으로 매번 재생성.
**변경 로직**:
1. 엔진들을 `Household` 클래스의 클래스 변수로 이동 (1회 초기화).
2. 인스턴스 메서드에서는 `self._lifecycle_engine` (클래스 변수 상속)으로 접근 가능하므로 코드 변경 최소화 가능(선택적), 혹은 명시적으로 `self.__class__._lifecycle_engine`을 사용.
3. `__init__`에서 `goods_data`를 파싱하여 `goods_info_map`을 만드는 부분을 제거. 대신 `Factory` 혹은 `Builder`에서 생성된 참조를 주입받아 사용.

**Diff Example**:
```python
class Household(...):
    # --- Class Variables: Stateless Engines (Singleton per Class) ---
    _lifecycle_engine = LifecycleEngine()
    _needs_engine = NeedsEngine()
    _social_engine = SocialEngine()
    _budget_engine = BudgetEngine()
    _consumption_engine = ConsumptionEngine()
    _belief_engine = BeliefEngine()
    _crisis_engine = CrisisEngine()
    _housing_connector = HousingConnector()

    def __init__(self, ..., goods_data: List[Dict[str, Any]], goods_info_map: Optional[Dict[str, Any]] = None, ...):
        # Remove engine instantiations from here
        # self.lifecycle_engine = LifecycleEngine() # [REMOVED]
        
        # Share goods_info_map reference instead of regenerating
        if goods_info_map is not None:
            self.goods_info_map = goods_info_map
        else:
            self.goods_info_map = {g["id"]: g for g in goods_data} # Fallback for legacy tests
```

### B. `simulation/decisions/ai_driven_household_engine.py` (AIDrivenHouseholdDecisionEngine)
**문제점**: `__init__`에서 3개의 Manager 객체를 인스턴스별로 생성.
**변경 로직**:
1. `ConsumptionManager`, `LaborManager`, `AssetManager`를 클래스 변수로 승격.
2. Manager들의 메서드는 철저히 인자로 받은 `Context` 객체에 의존하여 상태를 변경하므로 부작용 없음.

**Diff Example**:
```python
class AIDrivenHouseholdDecisionEngine(BaseDecisionEngine):
    # --- Class Variables: Managers (Singleton per Class) ---
    _consumption_manager = ConsumptionManager()
    _labor_manager = LaborManager()
    _asset_manager = AssetManager()

    def __init__(self, ...):
        # self.consumption_manager = ConsumptionManager() # [REMOVED]
        pass
    
    def _make_decisions_internal(...):
        # Use class variables
        survival_override_result = self._consumption_manager.check_survival_override(...)
```

### C. `simulation/firms.py` (Firm) - *Assumption based on Firm Pattern Consistency*
**문제점**: `Firm` 역시 Orchestrator로서 `ProductionEngine`, `FinanceEngine`, `HREngine` 등을 `self`로 초기화할 확률이 매우 높음.
**변경 로직**:
1. `Firm` 클래스 내부의 모든 엔진을 클래스 변수로 이동.

### D. `simulation/factories/` 또는 `modules/system/builders/simulation_builder.py`
**문제점**: 에이전트를 대량 생성할 때 `goods_info_map` 참조를 넘겨주지 않음.
**변경 로직**:
1. 팩토리 혹은 빌더 초기화 시점에 전역 `goods_info_map`을 1회 생성 (`shared_goods_info_map = {g['id']: g for g in goods_data}`).
2. `Household` 및 `Firm` 생성자에 `goods_info_map=shared_goods_info_map` 파라미터 전달.

---

## 3. 인터페이스 명세 (Interface Specifications & Exceptions)

- **DTO Purity / Exception**: 본 수정은 데이터 구조(DTO)나 예외(Exception) 자체를 변경하지 않습니다. 기존 `DecisionContext`, `LifecycleInputDTO` 구조는 완벽히 유지됩니다. 
- **Type Hinting**: `Household` 생성자에 `goods_info_map: Optional[Dict[str, Any]] = None` 시그니처가 추가됩니다.

---

## 4. 🚨 정합성 부채 (Conceptual Debt)

- **Engine State Pollution Risk**: 만약 기존 엔진(`LifecycleEngine` 등) 내부 `__init__`이나 메서드에서 `self.some_var = ...` 형태로 상태를 임시 캐싱하는 코드가 숨어있었다면, 클래스 레벨 공유 시 에이전트 간 데이터 오염(Race Condition / Cross-contamination)이 발생합니다.
- **Action**: 구현 전/후로 모든 Engine 클래스와 Manager 클래스의 `__init__` 및 메서드들을 전수 스캔하여 인스턴스 상태(`self.attribute`)를 런타임에 변경하는지(Mutation) 반드시 `Vibe Check`해야 합니다. 상태가 없음을 보장해야만 본 패턴 적용이 안전합니다. (기대치: 모두 파라미터 기반 순수 함수형 클래스여야 함).

---

## 5. 검증 계획 (Testing & Verification Strategy)

- **New Test Cases**:
  - `test_household_engine_singleton`: 두 개의 독립된 `Household` 인스턴스를 생성한 뒤, `agent1._lifecycle_engine is agent2._lifecycle_engine` 인지 참조(Identity)가 동일한지 단언(Assert)합니다.
  - `test_household_goods_map_shared`: 에이전트들의 `goods_info_map` 객체 참조 `id()`가 일치하는지 테스트합니다.
- **Integration Check**: 
  - `pytest tests/integration/` 전체 실행 시 로직 변경으로 인한 에러가 발생하지 않아야 합니다. 특히, `make_decision` 로직에서 엔진이 공용 참조됨으로써 발생하는 오작동이 없는지 확인합니다.
  - `NUM_HOUSEHOLDS=2000` 이상 대규모 시뮬레이션을 1틱 실행하여 `MemoryError`가 발생하는지, 혹은 프로파일러 상 객체 수가 획기적으로 줄었는지(Agent Bloat 완화) 관측해야 합니다.

---

## 6. Mocking Guide (테스트 영향도)

- **Mock 객체 교체 이슈**: 
  기존 테스트 중 `household.lifecycle_engine = MagicMock()` 형태로 특정 에이전트의 엔진만 모킹하여 테스트하던 코드가 있다면, 이제 클래스 변수이므로 `patch.object(Household, '_lifecycle_engine')` 방식으로 모킹 패러다임을 전환해야 합니다.
- **Fixture 수정 권고**:
  `tests/conftest.py` 등에서 수동으로 `Household`를 초기화할 때, `goods_info_map`을 명시적으로 넣어주거나 기본값 딕셔너리 생성이 작동하게 하여 파손(Break)을 방지합니다.

---

## 7. 🚨 Risk & Impact Audit (기술적 위험 분석)

- **순환 참조 및 모듈 로딩 시점 위험**: 클래스 변수로 `LifecycleEngine()` 등을 직접 할당할 때, 파일 최상단 임포트 순서(Import Resolution)에 따라 `LifecycleEngine`이 정의되지 않은 상태에서 `Household`가 로드되면 순환 참조 에러가 발생할 수 있습니다. 이미 상단에서 Engine들을 임포트 중이므로 문제는 적어보이나, 유의해야 합니다. 
- **설정 의존성 (Config Dependency)**: 일부 엔진이 초기화 시점에 파라미터를 요구한다면 (예: `NeedsEngine(config)`), 클래스 레벨 초기화가 불가능할 수 있습니다. 코드를 확인해보면 현재 모든 엔진은 인자가 없는 `__init__()`을 가지고, `process(input_dto)`에서 config를 받으므로(Stateless/Context Injection) 문제되지 않습니다.

---

## 8. 🚨 Mandatory Reporting Verification
- 본 작업과 관련된 기술 부채 확인, 엔진 상태 오염 검증 결과, 메모리 절감 수치, 그리고 테스트 패스 결과를 구현 완료 직후 반드시 `communications/insights/WO-SPEC-MEM-FIX-ENGINE-SINGLETON.md`에 독립된 파일로 기록할 것을 지시합니다. (이 지침이 누락되면 해당 미션은 Hard-Fail 처리됩니다.)

---

## 9. 🔍 [ANTIGRAVITY REVIEW] 보완 사항

> [!WARNING]
> **변수명 접두사 불일치**: 이 스펙은 `_lifecycle_engine` (언더스코어 접두사)을 사용하지만,
> 실제 코드(`core_agents.py:L118-125`)는 `self.lifecycle_engine` (접두사 없음)입니다.
> **기존 코드와의 호환성을 위해 접두사 없이 유지해야 합니다.**
> 접두사를 붙이면 `self.lifecycle_engine.process(...)` 형태의 모든 호출부를 수정해야 합니다.

### 확인된 사실
- ✅ **Section A (Household 8 Engines)**: `core_agents.py:L118-125`에서 실제로 8개 엔진이 per-agent 인스턴스로 생성됨 확인.
- ✅ **Section B (3 Managers)**: `ai_driven_household_engine.py:L38-40`에서 실제 확인.
- ✅ **Section D (goods_info_map)**: `core_agents.py:L218`에서 dict comprehension 복사 확인.
- ⚠️ **Section C (Firm)**: 추정 기반. 구현 전 Firm 소스 전수 확인 필요.

### 스펙 중복 정리
- `WO-SPEC-MEM-SINGLETON-HOUSEHOLD` 스펙이 Section A+D를 더 상세히 커버합니다.
- **구현 시 SINGLETON_HOUSEHOLD 스펙을 우선 참조**하고, 이 스펙의 Section B(매니저)와 C(Firm)는 별도 미션으로 진행.

### 수정된 Diff (접두사 없는 버전)
```python
class Household(...):
    # --- Class Variables: Stateless Engines (Singleton per Class) ---
    lifecycle_engine = LifecycleEngine()
    needs_engine = NeedsEngine()
    social_engine = SocialEngine()
    budget_engine = BudgetEngine()
    consumption_engine = ConsumptionEngine()
    belief_engine = BeliefEngine()
    crisis_engine = CrisisEngine()
    housing_connector = HousingConnector()
    
    # __init__에서 L118-125의 8줄 삭제
```