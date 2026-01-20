# 📖 Code Review Report: Finance-Params-Migration

## 🔍 Summary
이 PR은 하드코딩된 금융 관련 상수를 `config/economy_params.yaml` 파일로 이전하는 작업을 성공적으로 수행했습니다. 그러나 동시에 다수의 `scripts/` 파일에서 경로 처리 로직을 수정했는데, 이는 원래의 리팩토링 목표(TD-063: `pathlib` 사용)와 상반되는 방향으로 진행되어 코드 스타일의 퇴보를 야기했습니다. 또한, 관련 없는 두 개의 작업(금융 파라미터 이전, 인프라 정리)이 하나의 PR에 혼합되었습니다.

## 🚨 Critical Issues
- 발견되지 않았습니다.

## ⚠️ Logic & Spec Gaps
1.  **Spec 위반 및 코드 스타일 퇴보**:
    - **위치**: `scripts/` 폴더 내의 모든 변경된 파일 (e.g., `diagnose_deadlock.py`, `iron_test.py`, `verify_banking.py` 등).
    - **문제**: 이 PR에 포함된 인프라 정리(TD-063)의 목표는 `sys.path` 조작 시 `pathlib`을 사용하도록 통일하는 것이었습니다. 그러나 변경된 코드는 현대적이고 안정적인 `pathlib` 사용을 제거하고, 상대적으로 취약한 `os.path` 조합으로 되돌아갔습니다. 이는 명백한 스펙 위반이며 코드 품질의 퇴보입니다.
    ```diff
    - sys.path.append(str(Path(__file__).resolve().parent.parent))
    + sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    ```
2.  **관심사 분리(SoC) 원칙 위반**:
    - **위치**: PR 전체
    - **문제**: "금융 파라미터 이전"이라는 명확한 목표를 가진 PR에, 별개의 작업인 "스크립트 경로 수정"이 포함되었습니다. 두 작업은 서로 다른 기술 부채(TD-034/TD-041 vs TD-063)에 해당하므로 별도의 PR로 분리하여 관리하는 것이 바람직합니다.

3.  **문서 플레이스홀더 재도입**:
    - **위치**: `design/drafts/draft_Write_a_Zero_Question_Implemen.md`
    - **문제**: 문서 내 `WO-079`가 `WO-XXX`로 변경되었습니다. 다른 작업(TD-051)에서 이러한 플레이스홀더를 제거하도록 되어 있는 만큼, 이는 프로젝트 관리의 일관성을 해치는 변경입니다.

## 💡 Suggestions
1.  **테스트 코드의 하드코딩**:
    - **위치**: `tests/modules/finance/test_system.py`
    - **제안**: `test_grant_bailout_loan` 테스트에서 상환 비율을 `0.5`로 단언하고, `test_service_debt_central_bank_repayment`에서 채권 만기를 `400 / 48`로 하드코딩했습니다. 이 값들을 `mock_config`에서 가져오도록 수정하면, 향후 설정값이 변경되더라도 테스트 코드를 유지보수하기 용이해집니다.
    ```python
    # 변경 전
    assert loan.covenants.mandatory_repayment == 0.5
    bond_lifetime_years = 400 / 48
    
    # 변경 후 (예시)
    assert loan.covenants.mandatory_repayment == mock_config.get("economy_params.bailout_repayment_ratio")
    bond_maturity = mock_config.get("economy_params.bond_maturity_ticks")
    ticks_per_year = mock_config.TICKS_PER_YEAR
    bond_lifetime_years = bond_maturity / ticks_per_year
    ```

## ✅ Verdict
- **REQUEST CHANGES**

금융 상수 이전 작업은 올바르게 수행되었으나, 스펙에 위배되는 스크립트 수정과 여러 관심사가 혼합된 점을 수정해야 합니다. 이 PR을 **1) 금융 설정 이전**과 **2) `pathlib`을 올바르게 사용한 스크립트 경로 수정**으로 분리하여 다시 제출해 주십시오.
