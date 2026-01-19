# 🔍 Git Diff Review: `phase29-depression`

## 🔍 Summary

이번 변경은 시스템에 '대공황' 시나리오를 도입하는 것을 주요 골자로 합니다. 설정 파일을 통해 특정 시점(`tick: 50`)에 높은 이자율과 법인세율을 적용하는 재정 및 통화 충격을 가합니다. 또한, 기업의 재무 건전성을 Altman Z-Score로 평가하여 파산 위험을 추적하는 `CrisisMonitor` 모듈을 추가하고, 관련 테스트 코드를 통해 시나리오가 정상적으로 작동하는지 검증합니다.

## 🚨 Critical Issues

1.  **[CRITICAL] 시나리오 설정 파일 경로 하드코딩**
    *   **File**: `simulation/initialization/initializer.py`
    *   **Code**: `scenario_path = "config/scenarios/phase29_depression.json"`
    *   **Issue**: 시뮬레이션 초기화 로직에 특정 시나리오 파일의 경로가 하드코딩되어 있습니다. 이로 인해 다른 시나리오를 실행하거나 설정을 변경하기 위해 매번 코드를 수정해야 합니다. 이는 유연성을 심각하게 저해하며, 설정 주입(Configuration Injection) 원칙에 위배됩니다.

2.  **[CRITICAL] 테스트 결과물(Artifact) 커밋**
    *   **File**: `reports/crisis_monitor_0.csv`
    *   **Issue**: 테스트 실행 결과로 생성된 CSV 파일이 원격 저장소에 포함되었습니다. 이러한 결과물은 실행 환경마다 달라질 수 있으며, 저장소 용량을 불필요하게 차지하고 코드 변경 내역을 추적하기 어렵게 만듭니다. 해당 경로는 `.gitignore`에 추가되어야 합니다.

## ⚠️ Logic & Spec Gaps

1.  **불안정한 데이터 추출 로직**
    *   **File**: `modules/analysis/crisis_monitor.py`
    *   **Method**: `_calculate_z_score_for_firm`
    *   **Issue**: Z-Score 계산을 위해 `Firm` 객체의 재무 데이터를 가져올 때 `hasattr`를 과도하게 사용하고 있습니다. 이는 `Firm` 객체의 명확한 인터페이스가 부재함을 시사하며, `Firm`의 내부 구조가 변경될 경우 `CrisisMonitor`가 쉽게 깨질 수 있는 불안정한 결합(brittle coupling)을 만듭니다.

2.  **중복된 정책 적용 로직**
    *   **File**: `simulation/systems/event_system.py`
    *   **Issue**: 통화 충격을 적용할 때, `central_bank.base_rate`를 수정한 뒤 다시 `bank.update_base_rate()`를 직접 호출하고 있습니다. 주석에도 명시되었듯, 이는 데이터 흐름에 대한 불확실성을 나타내며 중복 실행의 가능성이 있습니다. Spec에서 'Dirty Hack'이 허용되었더라도, 명확하고 단일한 지점에서 정책을 강제하는 것이 바람직합니다.

## 💡 Suggestions

1.  **설정 관리 개선**
    *   `SimulationInitializer`가 시나리오 파일 경로를 외부에서 인자(argument)로 받거나, `config/scenarios/` 디렉토리 내 활성화된(`is_active: true`) 시나리오 파일을 동적으로 탐색하도록 리팩토링하는 것을 권장합니다.

2.  **관심사 분리(SoC) 및 인터페이스 강화**
    *   `Firm` 클래스 내부에 재무 데이터를 DTO(Data Transfer Object) 형태로 반환하는 메서드(예: `get_financial_snapshot()`)를 추가하십시오. `CrisisMonitor`는 이 메서드를 호출하여 안정적으로 데이터를 얻어오도록 수정하면 결합도를 낮추고 코드의 안정성을 높일 수 있습니다.

3.  **테스트 환경 개선**
    *   `test_phase29_depression.py`의 `tearDown`에서 리포트 파일을 직접 삭제하는 대신, 테스트 중 생성되는 파일은 임시 디렉토리에 저장하고 테스트 종료 후 일괄적으로 정리하는 프레임워크 기능을 활용하는 것이 좋습니다.

## ✅ Verdict

**REQUEST CHANGES**

기능의 핵심 로직과 테스트는 잘 구현되었으나, 설정 파일 경로 하드코딩과 같은 심각한 설계 문제가 발견되었습니다. 해당 이슈들을 수정한 후 다시 리뷰를 요청해 주십시오.
