# MISSION_SPEC: DecisionEngine Manager Singleton

**Mission Key**: WO-SPEC-MEM-SINGLETON-DECISION
**Target Phase**: Memory Optimization & Refactoring
**Written by**: Antigravity (직접 작성 — Gemini OOM으로 인해)

## 1. 개요 (Overview)

`AIDrivenHouseholdDecisionEngine.__init__`에서 3개의 Manager 객체가 per-agent로 인스턴스화되는 구조를 클래스 변수(Class Variable)로 전환합니다. N개 에이전트 기준 3N개 매니저 객체 → 3개로 절감됩니다.

**Firm의 `CorporateManager`는 이번 미션 범위에서 제외합니다** — `config_module`과 `logger`를 생성자에서 받아 인스턴스 상태로 저장하므로, 단순 클래스 변수 전환이 불가능합니다.

---

## 2. 대상 분석 (Statelessness Verification)

### ✅ 전환 대상 (Household)

| Manager | `__init__` 파라미터 | 인스턴스 상태 | Stateless 여부 |
|---------|-------------------|-------------|---------------|
| `ConsumptionManager` | 없음 | 없음 | ✅ Stateless |
| `LaborManager` | 없음 | 없음 | ✅ Stateless |
| `AssetManager` | 없음 | `self.stock_trader = StockTrader()` | ✅ StockTrader도 Stateless¹ |

¹ `AssetManager.stock_trader`는 sub-object이지만, `StockTrader`의 모든 메서드는 컨텍스트 객체를 파라미터로 받아 처리하므로 Stateless 패턴에 해당합니다. 클래스 변수 전환 시 안전합니다.

### ❌ 전환 제외 (Firm)

| Manager | 제외 사유 |
|---------|----------|
| `CorporateManager` | `__init__(config_module, logger)` — `self.config_module` 저장, 4개 sub-strategy 인스턴스화. 인스턴스별 config이 다를 수 있으므로 공유 불가. |

---

## 3. 파일별 변경 사항 (Detailed Changes)

### A. `simulation/decisions/ai_driven_household_engine.py`

**현재 코드** (L38-41):
```python
def __init__(self, ai_engine, config_module, logger=None):
    ...
    # Initialize Managers
    self.consumption_manager = ConsumptionManager()
    self.labor_manager = LaborManager()
    self.asset_manager = AssetManager()
```

**변경 후**:
```python
class AIDrivenHouseholdDecisionEngine(BaseDecisionEngine):
    # --- Class-Level Stateless Managers (Singleton per Class) ---
    consumption_manager = ConsumptionManager()
    labor_manager = LaborManager()
    asset_manager = AssetManager()

    def __init__(self, ai_engine, config_module, logger=None):
        self.ai_engine = ai_engine
        self.config_module = config_module
        self.logger = logger if logger else logging.getLogger(__name__)
        # [DELETED] self.consumption_manager = ConsumptionManager()
        # [DELETED] self.labor_manager = LaborManager()
        # [DELETED] self.asset_manager = AssetManager()

        self.logger.info(
            "AIDrivenHouseholdDecisionEngine initialized (Modularized).",
            extra={"tick": 0, "tags": ["init"]},
        )
```

**변경 범위**: L25-46 (클래스 body + `__init__` 수정)

**호출 호환성**: 기존 코드에서 `self.consumption_manager.check_survival_override(...)` 등 `self.` 접근 패턴이 유지됩니다. Python의 속성 탐색 순서(인스턴스 → 클래스)에 의해 클래스 변수도 `self.`로 접근 가능합니다.

---

## 4. 인터페이스 명세 (Interface Specifications)

- 기존 DTO/API 변경 없음
- `__init__` 시그니처 변경 없음
- `BaseDecisionEngine` 프로토콜 위반 없음

---

## 5. 검증 계획 (Testing & Verification)

### 5.1 New Test Cases
```python
def test_decision_engine_manager_singleton():
    """3개 매니저가 클래스 변수로 공유되는지 확인."""
    engine1 = AIDrivenHouseholdDecisionEngine(mock_ai, mock_config)
    engine2 = AIDrivenHouseholdDecisionEngine(mock_ai, mock_config)
    
    assert engine1.consumption_manager is engine2.consumption_manager
    assert engine1.labor_manager is engine2.labor_manager
    assert engine1.asset_manager is engine2.asset_manager
```

### 5.2 Integration Check
- `pytest tests/ -x --timeout=60` 전체 통과
- 기존 `test_ai_driven_*` 테스트 호환 확인

---

## 6. Mocking Guide (테스트 영향도)

기존에 `engine.consumption_manager = MagicMock()` 형태의 인스턴스 모킹이 있다면:

**기존 패턴** (인스턴스 할당 — 여전히 작동):
```python
engine.consumption_manager = MagicMock()  # 인스턴스에 직접 할당하면 클래스 변수를 가림
```
> Python 속성 탐색 순서에 의해, `self.consumption_manager = MagicMock()` 할당은 인스턴스 수준에서 클래스 변수를 "shadow"합니다. 따라서 **기존 테스트 모킹 패턴은 깨지지 않습니다.**

**권장 패턴** (context manager):
```python
with patch.object(AIDrivenHouseholdDecisionEngine, 'consumption_manager') as mock_cm:
    mock_cm.check_survival_override.return_value = None
    # test...
```

---

## 7. Risk & Impact Audit

- **상태 오염 위험**: 매니저 내부에서 `self.some_var = ...` 형태로 런타임 상태를 변경하면 에이전트간 오염 발생. 확인 결과: `ConsumptionManager`, `LaborManager`는 인스턴스 상태 없음. `AssetManager.stock_trader`는 `StockTrader()` 인스턴스이나, StockTrader도 컨텍스트 기반 순수 함수형.
- **순환 참조 위험**: 없음. Manager import는 이미 파일 상단에서 수행 중.
- **Firm 제외**: `CorporateManager`는 `config_module` 의존성으로 인해 별도 미션에서 DI(Dependency Injection) 패턴 적용 필요.

---

## 8. 🚨 Mandatory Reporting Verification
구현 완료 후 반드시 `communications/insights/WO-SPEC-MEM-SINGLETON-DECISION.md`에 인사이트 보고서를 작성할 것.
