# 🔍 Git Diff Review: WO-115 Stability Verification & Architectural Regression

---

### 🔍 Summary

이 PR은 'Great Reset' 시나리오의 안정성을 검증하기 위한 강력한 테스트 스크립트(`verify_great_reset_stability.py`)를 추가하여, 제로섬(Zero-Sum) 위반을 감지하는 중요한 기능을 도입했습니다. 하지만 동시에, 의사결정 엔진의 "DTO Purity Gate" 아키텍처를 전면적으로 제거하고 관련 테스트를 삭제하여 심각한 구조적 기술 부채를 발생시키는 상충된 변경 사항을 포함하고 있습니다.

---

### 🚨 Critical Issues

1.  **아키텍처 원칙 파괴 및 테스트 삭제 (CRITICAL)**:
    - **파일**: `simulation/decisions/corporate_manager.py`, `simulation/decisions/rule_based_firm_engine.py`, `simulation/firms.py`, `tests/test_purity_gate.py` (삭제됨)
    - **문제**: 의사결정 로직(순수 함수)과 상태 변경(부수 효과)을 분리하는 핵심 아키텍처 원칙인 "DTO Purity Gate"가 폐기되었습니다. 이제 의사결정 엔진은 읽기 전용 `FirmStateDTO` 대신 전체 `Firm` 객체를 직접 참조하여 내부 상태를 수정합니다.
    - **영향**: 이 변경은 의사결정 로직을 테스트하기 어렵게 만들고, 예측 불가능한 부수 효과를 유발할 위험을 다시 도입합니다.
    - **가장 심각한 문제**: 이 아키텍처를 강제하던 핵심 테스트 파일인 **`tests/test_purity_gate.py`가 삭제되었습니다.** 이는 기술 부채를 의도적으로 도입하고 회귀를 방지할 안전장치를 제거하는 매우 위험한 행위입니다.

---

### ⚠️ Logic & Spec Gaps

1.  **일관성 없는 설계 철학**:
    - **긍정적**: 새로 추가된 `verify_great_reset_stability.py` 스크립트는 `h.create_state_dto().assets` 와 같이 DTO와 공개 인터페이스를 사용하여 캡슐화 원칙을 존중하는, 매우 잘 작성된 코드입니다.
    - **부정적**: 반면, 의사결정 엔진들은 `firm.finance.invest_in_rd()` 와 같이 내부 컴포넌트의 메서드를 직접 호출하여 캡슐화를 정면으로 위반합니다.
    - 이 두 가지 상반된 접근 방식이 하나의 PR에 공존하는 것은 프로젝트의 아키텍처 방향성에 대한 혼란을 야기합니다.

2.  **"내부 주문" 패턴의 폐기**:
    - **파일**: `simulation/firms.py`, `simulation/decisions/corporate_manager.py`
    - **문제**: 의사결정 엔진이 `Order(..., market_id="internal")`을 반환하고 `Firm`이 이를 해석하여 실행하던 "내부 주문(Internal Order)" 패턴이 제거되었습니다. 이는 상태 변경의 책임을 다시 의사결정 로직으로 되돌려, SoC(관심사 분리) 원칙을 위반합니다.

---

### 💡 Suggestions

1.  **DTO Purity Gate 복구 계획 수립**:
    - 이 아키텍처 회귀는 심각한 기술 부채입니다. 이를 해결하기 위한 **별도의 Work Order를 즉시 생성**하고 로드맵을 수립해야 합니다. 만약 기존 "내부 주문" 패턴에 결함이 있었다면, 전체 원칙을 폐기할 것이 아니라 패턴을 개선하는 방향으로 접근해야 합니다.
2.  **삭제된 테스트 복원**:
    - 삭제된 `tests/test_purity_gate.py` 파일은 즉시 복원되어야 합니다. 당장 통과시킬 수 없다면, 관련 테스트들을 `@pytest.mark.skip`으로 표시하고, 아키텍처 복구 WO를 참조하는 `TODO` 주석을 남겨야 합니다. **테스트를 삭제하는 것은 해결책이 될 수 없습니다.**
3.  **안정성 검증 스크립트 CI 통합**:
    - 새로 추가된 `verify_great_reset_stability.py`는 매우 훌륭하며, 향후의 제로섬 위반을 막기 위해 CI 파이프라인에 통합하여 자동으로 실행되도록 하는 것을 강력히 권장합니다.

---

### ✅ Verdict

**REQUEST CHANGES**

**이유**: 새로운 안정성 검증 스크립트 추가는 매우 중요한 진전이지만, 프로젝트의 핵심 아키텍처 원칙을 무너뜨리고 이를 강제하던 테스트까지 삭제한 것은 매우 심각한 회귀입니다. 이 PR은 상당한 위험과 기술 부채를 포함하고 있어 이대로 병합될 수 없습니다. 최소한, 이로 인해 발생한 아키텍처 부채를 해결하기 위한 공식적인 계획(예: 새로운 Work Order 생성)이 수립되고 연결된 후에 재검토되어야 합니다.
