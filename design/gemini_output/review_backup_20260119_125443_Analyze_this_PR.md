# 🔍 Git Diff Review: `phase29-depression`

## 🔍 Summary

이번 변경은 시뮬레이션에 '대공황' 시나리오를 도입합니다. 새로운 `CrisisMonitor` 모듈이 추가되어 Altman Z-Score를 사용해 기업의 재무 건전성을 추적합니다. 시나리오는 JSON 설정 파일(`phase29_depression.json`)을 통해 정의되며, `EventSystem`이 지정된 시점에 금리 인상(통화 충격)과 법인세 인상(재정 충격)을 가하여 시나리오를 발동시킵니다. 관련 로직을 검증하기 위한 테스트 코드도 추가되었습니다.

## 🚨 Critical Issues

1.  **보안/하드코딩: 설정 파일 경로 하드코딩**
    - **파일**: `simulation/initialization/initializer.py`
    - **라인**: `scenario_path = "config/scenarios/phase29_depression.json"`
    - **문제**: 시나리오 설정 파일의 경로가 코드 내에 하드코딩되어 있습니다. 이는 유연성을 저해하며, 파일 위치가 변경될 경우 코드를 직접 수정해야 하는 문제를 야기합니다. 설정 경로는 외부 설정 관리자를 통해 주입받는 것이 바람직합니다.

2.  **보안/관리: 생성된 결과 파일 포함**
    - **파일**: `reports/crisis_monitor_0.csv`
    - **문제**: 시뮬레이션 실행 결과로 생성된 `csv` 파일이 Git 저장소에 포함되었습니다. 이러한 결과 파일은 버전 관리 대상이 아니며, `.gitignore`에 추가하여 추적되지 않도록 해야 합니다.

## ⚠️ Logic & Spec Gaps

1.  **아키텍처: 모듈 간 강한 결합 (Tight Coupling)**
    - **파일**: `modules/analysis/crisis_monitor.py`
    - **함수**: `_calculate_z_score_for_firm`
    - **문제**: `CrisisMonitor`가 `Firm` 객체의 내부 속성(`assets`, `inventory`, `total_debt` 등)에 `hasattr`를 사용해 직접 접근하고 있습니다. 이는 `Firm` 클래스의 내부 구현에 강하게 의존하는 방식으로, 향후 `Firm`의 구조가 변경될 때 `CrisisMonitor` 코드가 예기치 않게 오작동할 수 있습니다.
    - **권장**: `Firm` 클래스에 재무 상태를 나타내는 DTO(Data Transfer Object)나 구조화된 데이터를 반환하는 메서드(예: `get_financial_statement()`)를 추가하고, `CrisisMonitor`는 이 메서드를 통해 데이터를 얻도록 리팩토링하는 것이 좋습니다.

2.  **로직: 불필요한 중복 할당**
    - **파일**: `simulation/initialization/initializer.py`
    - **라인**: `sim.crisis_monitor.run_id = sim.run_id` (L235, L281)
    - **문제**: `CrisisMonitor`의 `run_id`가 두 번 할당됩니다. 첫 할당 시점에는 `sim.run_id`가 생성되지 않았을 수 있으므로, `run_id`가 확정된 이후 한 번만 할당해야 합니다.

3.  **아키텍처: "Dirty Hack"을 통한 상태 변경**
    - **파일**: `simulation/systems/event_system.py`
    - **문제**: `EventSystem`이 `central_bank.base_rate`와 `government.corporate_tax_rate` 속성을 직접 수정합니다. 주석에 'Spec에 명시된 "Dirty Hack"'이라고 언급되어 있지만, 이는 중앙 에이전트의 상태를 외부에서 직접 제어하는 방식으로 캡슐화를 위반하며 유지보수를 어렵게 만듭니다.
    - **권장**: 명시적인 API(예: `central_bank.override_base_rate(...)`)를 통해 상태를 변경하도록 설계하는 것이 장기적으로 더 안정적입니다.

## 💡 Suggestions

1.  **테스트 격리성 강화**
    - **파일**: `tests/test_phase29_depression.py`
    - **제안**: 현재 테스트는 실제 `json` 파일에 의존하고 있습니다. `config_manager`를 모킹(Mocking)하는 것과 같이 시나리오 설정 자체를 모킹하여 테스트가 외부 파일 의존성 없이 완전히 독립적으로 실행되도록 개선하는 것이 좋습니다. 또한 테스트 중 생성되는 파일은 pytest의 `tmp_path`와 같은 임시 디렉토리를 사용하도록 수정하는 것을 권장합니다.

2.  **하드코딩된 경로 제거**
    - **파일**: `tests/test_phase29_depression.py` (`report_file` 경로)
    - **제안**: 테스트 코드 내의 `reports/` 경로 역시 하드코딩되어 있습니다. 테스트 환경에서는 동적으로 임시 경로를 생성하여 사용하는 것이 이상적입니다.

## ✅ Verdict

**REQUEST CHANGES**

위에 언급된 **Critical Issues**는 반드시 수정되어야 합니다. 특히 하드코딩된 경로와 결과 파일의 Git 포함 문제는 즉시 해결이 필요합니다. 'Logic & Spec Gaps'와 'Suggestions'에 제안된 내용들은 코드의 안정성과 유지보수성을 높이기 위한 강력한 권장 사항이므로 함께 검토 후 반영해 주시기 바랍니다.
