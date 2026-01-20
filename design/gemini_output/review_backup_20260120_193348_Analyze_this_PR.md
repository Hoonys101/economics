# 🔍 Git Diff 리뷰 보고서: `finance-params-migration`

---

## 🔍 Summary

본 변경 사항은 하드코딩된 금융 관련 파라미터들을 `economy_params.yaml` 설정 파일로 이전하는 작업을 핵심으로 합니다. 이 과정에서 `modules/finance/system.py`가 새로운 `ConfigManager`를 사용하도록 성공적으로 리팩토링되었습니다.

그러나, 함께 포함된 스크립트 경로 수정 및 문서 정리 작업에서 **원래의 요구사항과 반대되는 변경(Regression)**이 다수 발견되어 수정이 반드시 필요합니다.

## 🚨 Critical Issues

- **요구사항 위반 (Path Refactoring)**: `scripts/` 내의 거의 모든 파일에서 `sys.path`를 조작하는 방식이 변경되었습니다.
  - **문제점**: 원본 미션(TD-063)에서는 `pathlib`을 사용하여 경로 탐지 로직을 안정화하라고 명시했지만, 실제 변경은 `os.path.abspath`, `os.getcwd()` 등 다양한 방식으로 구현되었으며, `pathlib` 사용은 오히려 제거되었습니다. 이는 유지보수성을 저하시키고 미션의 핵심 목표를 위반합니다.
  - **위치**: `scripts/diagnose_deadlock.py`, `scripts/experiments/*.py`, `scripts/failure_diagnosis.py` 등 Diff에 포함된 대부분의 `scripts` 파일.
  - **예시**:
    ```diff
    -from pathlib import Path
    ...
    -sys.path.append(str(Path(__file__).resolve().parent.parent))
    +sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    ```

- **요구사항 위반 (Documentation Sanitization)**: 문서 내 플레이스홀더를 제거하는 요구사항(TD-051)과 반대로, 실제 ID를 플레이스홀더로 되돌리는 변경이 포함되었습니다.
  - **문제점**: `WO-079`라는 구체적인 Work Order ID가 `WO-XXX`라는 플레이스홀더로 변경되었습니다.
  - **위치**: `design/drafts/draft_Write_a_Zero_Question_Implemen.md`
  - **예시**:
    ```diff
    - # [Refactor] Work Order: WO-079 - 설정 중앙화 및 시나리오 로더 구현
    + # [Refactor] Work Order: WO-XXX - 설정 중앙화 및 시나리오 로더 구현
    ```

## ⚠️ Logic & Spec Gaps

- **테스트 코드 내 하드코딩**: 금융 파라미터 이전은 잘 되었으나, 관련된 테스트 코드 내에 여전히 숫자값이 하드코딩되어 있습니다.
  - **문제점**: `mock_config`를 통해 설정값을 모킹했음에도 불구하고, `assert` 구문에서는 `0.5`, `400 / 48`과 같은 매직 넘버를 직접 사용합니다. 이로 인해 향후 설정값이 변경될 때 테스트 코드가 깨지기 쉽습니다.
  - **위치**: `tests/modules/finance/test_system.py`
  - **예시**:
    ```diff
    -    assert loan.covenants.mandatory_repayment == mock_config.BAILOUT_REPAYMENT_RATIO
    +    assert loan.covenants.mandatory_repayment == 0.5
    ```

- **범위 이탈 변경 (Scope Creep)**: 금융 파라미터 마이그레이션과 직접적인 관련이 없는 것으로 보이는 변경사항들이 다수 포함되어 있습니다.
  - **내용**: `simulation/core_agents.py` 및 `modules/household/dtos.py` 등에서 `is_homeless`, `social_status`, `current_consumption` 등의 속성 추가.
  - **의견**: 이 변경들이 다른 작업의 일부라면 별도의 PR로 분리하는 것이 좋습니다. 하나의 PR은 하나의 목적에 집중해야 리뷰와 추적이 용이합니다.

## 💡 Suggestions

- **Path Refactoring 재작업**: `scripts/` 폴더 내의 모든 `sys.path` 수정 로직을 미션 요구사항(TD-063)에 명시된 대로 `pathlib`을 사용하여 일관되게 재작성하십시오.
- **테스트 코드 개선**: `tests/modules/finance/test_system.py`의 `assert`문에서 하드코딩된 숫자 대신, `mock_config.get()`을 통해 반환되는 값을 사용하도록 수정하여 테스트의 유연성을 확보하십시오.
  - **예시**:
    ```python
    # 변경 제안
    repayment_ratio = mock_config.get("economy_params.bailout_repayment_ratio")
    assert loan.covenants.mandatory_repayment == repayment_ratio
    ```
- **Observer 스캔 로직 개선**: `scripts/observer/scan_codebase.py`에서 `scripts/observer` 디렉토리를 제외하는 로직이 특정 OS 경로 구분자(`\\`)에 의존하고 있어 불안정합니다. `os.path.normpath`나 `pathlib`을 사용하여 플랫폼에 독립적인 경로 비교 로직으로 개선하는 것을 권장합니다.

## ✅ Verdict

**REQUEST CHANGES**

핵심적인 파라미터 이전 작업은 잘 수행되었지만, 스크립트 경로 처리와 문서 ID 정리에서 미션 요구사항을 명백히 위반하는 심각한 회귀(Regression)가 발생했습니다. 위 Critical Issues와 Logic Gaps를 모두 수정한 후 다시 리뷰를 요청해 주십시오.
