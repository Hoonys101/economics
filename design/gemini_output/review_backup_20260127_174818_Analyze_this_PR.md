# 🔍 Code Review Report: WO-053 Tech Integration

## 🔍 Summary
이 변경 사항은 기술 개발 및 생산 단계를 `TickScheduler`에서 메인 시뮬레이션 루프로 이동시켜 오케스트레이션을 중앙화합니다. 이 과정에서 화폐 공급량 추적 방식에 중대한 논리적 변경이 발생했으며, 관련된 테스트 코드들이 개선되었습니다.

## 🚨 Critical Issues
- **없음.** 이 PR에서 심각한 보안 취약점이나 명백한 하드코딩은 발견되지 않았습니다.

## ⚠️ Logic & Spec Gaps
1.  **[CRITICAL] 잘못된 화폐 공급량(Money Supply) 추적 로직**
    - **파일**: `simulation/tick_scheduler.py` (L146)
    - **문제**: 경제 지표 추적 시, `money_supply` 인자로 `state.calculate_total_money()`를 사용하도록 변경되었습니다. `calculate_total_money()`는 시스템 전체의 화폐 총량을 반환하는 **무결성 검증용 함수**이며, 경제학적 의미의 통화량(M1, M2 등)이 아닙니다. 이 값은 리플럭스 시스템이나 중앙은행의 준비금 등 유통되지 않는 화폐까지 포함하므로, 이를 기반으로 계산되는 **화폐 유통 속도(Velocity of Money) 등의 지표가 심각하게 왜곡될 것입니다.** 이전의 `get_m2_money_supply`를 사용하거나 의도에 맞는 새로운 통화량 함수를 사용해야 합니다.
    - **영향**: 주요 경제 지표의 신뢰도 하락.

2.  **[HIGH] 화폐 시스템 무결성 검증 스크립트 삭제**
    - **파일**: `scripts/verify_td_111.py` (삭제됨)
    - **문제**: 이 스크립트는 시스템의 화폐 총량(`ws_total`)이 M2 통화량, 리플럭스 시스템 잔액, 중앙은행 잔고의 합과 일치하는지를 검증하는 중요한 **제로섬(Zero-Sum) 무결성 테스트**였습니다. 이 검증 로직이 `pytest` 기반의 영구적인 테스트로 이전되었다는 증거 없이 삭제되었습니다.
    - **영향**: 화폐가 의도치 않게 생성되거나 소멸하는 버그(Money Leak/Creation)를 감지할 수 있는 핵심적인 방어선이 사라졌습니다.

## 💡 Suggestions
1.  **테스트 코드 개선**
    - **파일**: `tests/integration/test_phase23_production.py`, `tests/systems/test_technology_manager.py`
    - **내용**: 기존의 복잡한 `fixture`와 `MagicMock` 의존성을 줄이고, 간단한 `MockConfig`와 헬퍼 함수를 사용하여 테스트를 재작성한 것은 매우 긍정적입니다. 테스트의 가독성과 유지보수성이 크게 향상되었습니다.

2.  **오케스트레이션 로직 캡슐화**
    - **파일**: `main.py`
    - **내용**: 기술 및 생산 로직을 메인 루프로 옮긴 것은 좋은 아키텍처 결정입니다. 다만, `next_tick`을 계산하는 등 세부 로직이 `main.py`에 노출되어 있습니다. 이 오케스트레이션 로직을 `Simulation` 클래스 내의 새로운 메소드(예: `sim.prepare_tick(next_tick)`)로 캡슐화하면 `main` 함수의 책임이 더 명확해지고 코드가 깔끔해질 것입니다.

## 🧠 Manual Update Proposal
- **Target File**: `design/platform_architecture.md`
- **Update Content**:
  아키텍처 문서의 시뮬레이션 루프 섹션에 다음 내용을 추가하여, 오케스트레이션 책임이 어디에 있는지 명확히 해야 합니다.

  ```markdown
  ### Tick Orchestration Model
  
  과거 `TickScheduler`에 혼재되어 있던 일부 핵심 프로세스는 시뮬레이션의 최상위 루프(`main.py`)로 이동하여 명시적으로 오케스트레이션됩니다. 이는 각 Tick의 주요 단계를 중앙에서 관리하고, 순서와 의존성을 명확히 하기 위함입니다.
  
  **주요 오케스트레이션 단계 (in `main.py`):**
  1.  **기술 발전 (Technology Update)**: `TechnologyManager`가 현재의 인적 자본 지수(Human Capital Index)와 기업 정보를 바탕으로 기술을 업데이트합니다.
  2.  **생산 (Production)**: 모든 기업이 업데이트된 기술 수준을 반영하여 상품을 생산합니다.
  3.  **Tick 실행 (Tick Execution)**: `TickScheduler`가 시장 거래, 이자 정산, 정부 활동 등 나머지 하위 단계들을 실행합니다.
  
  이 구조는 `TickScheduler`가 Tick 내의 "어떻게(How)"에 집중하고, 메인 루프가 "무엇을(What)"에 집중하는 SoC(관심사 분리) 원칙을 따릅니다.
  ```

## ✅ Verdict
**REQUEST CHANGES**

위에서 지적한 **두 가지 `Logic & Spec Gaps`**는 시스템의 핵심적인 경제 모델과 무결성에 직접적인 영향을 미치는 중대한 문제입니다. 해당 이슈들이 해결되기 전에는 이 변경 사항을 병합할 수 없습니다.
