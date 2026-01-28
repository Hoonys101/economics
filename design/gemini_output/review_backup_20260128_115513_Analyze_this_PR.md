# 🔍 Git Diff Review: WO-053

## 1. 🔍 Summary

시나리오 기반 파라미터 시스템을 도입하여 `phase23_industrial_rev`(산업 혁명) 시나리오를 구현하고, 이를 검증하기 위한 `verify_phase23.py` 스크립트를 추가하는 변경 사항입니다. 주된 목표는 기술 도입으로 인한 식량 과잉 공급과 가격 붕괴 현상을 시뮬레이션하는 것입니다. 그러나 구현 상의 치명적인 결함 두 가지가 발견되었습니다.

## 2. 🚨 Critical Issues

1.  **Zero-Sum 위반 (자산 소멸 버그)**: `verify_output.txt` 로그에서 시뮬레이션 진행 중 총 통화량이 비정상적으로 감소하여 음수 값(`Current: -777416.13`)으로 떨어지는 현상이 발견되었습니다. 이는 **치명적인 자산 소멸(Money Leak) 버그**를 의미합니다.
    - **위치**: 다수의 `FIRM_INACTIVE`, `FIRM_LIQUIDATION` 로그
    - **분석**: 기업 및 가계 청산 과정에서 보유 자산(재고, 자본 등)이 시장에 매각되어 회수되지 않고, 그대로 소멸(`Net Destruction: ...`, `Recovered: 0.00`) 처리되고 있습니다. 이는 시스템의 총 자산을 감소시켜 심각한 디플레이션과 경제 붕괴를 유발하는 원인입니다.

2.  **시나리오 파라미터 주입 실패**: 이번 작업의 핵심 기능인 시나리오 파라미터가 시뮬레이션에 제대로 적용되지 않고 있습니다.
    - **위치**: `simulation/initialization/initializer.py`, `scripts/verify_phase23.py`
    - **분석**: `initializer.py`는 시나리오 값을 레거시 `config` 객체에 `setattr`로 주입하지만, `TechnologyManager` 등 다른 모듈은 새로운 `ConfigManager`를 통해 값을 조회합니다. 두 설정 관리 방식이 혼용되면서 파라미터가 전달되지 않습니다. 그 결과 `verify_phase23.py` 테스트는 `Tech Multiplier: Not Set`을 출력하며, 시나리오의 핵심 로직(공급 과잉, 가격 하락)이 전혀 동작하지 않아 실패합니다.

## 3. ⚠️ Logic & Spec Gaps

1.  **복잡한 아키텍처 (Transaction → Order 변환)**: `commerce_system`에서 `PHASE23_MARKET_ORDER`라는 특수 트랜잭션을 생성하고, 이를 `phases` 모듈에서 다시 `Order` 객체로 변환하는 방식은 불필요하게 복잡하며 임시방편적입니다. `CommerceSystem`이 직접 `Order` 객체를 생성하도록 리팩토링해야 합니다.
    - **위치**: `simulation/orchestration/phases.py`, `simulation/systems/commerce_system.py`

2.  **하드코딩된 시장 개입**: `basic_food`의 가격을 강제로 억제하는 로직(`current_price * 0.8`)이 `phases.py`에 하드코딩되어 있습니다. 이는 시나리오의 결과를 인위적으로 만들어내는 "커브 피팅(Curve Fitting)"에 해당하며, 파라미터를 통해 에이전트의 행동을 유도하는 설계 원칙에 위배됩니다.
    - **위치**: `simulation/orchestration/phases.py`, `Phase1_Decision` 메소드

3.  **매직 넘버 사용**: `commerce_system.py`에서 주문 생성 시 `seller_id=999999`와 같은 매직 넘버가 사용되었습니다. 이는 시스템 예약 ID 등을 나타내는 명명된 상수로 대체되어야 합니다.

## 4. 💡 Suggestions

1.  **설정 관리 시스템 통일**: 레거시 `config` 객체와 `ConfigManager`로 이원화된 설정 관리 방식을 `ConfigManager`로 통일해야 합니다. `initializer.py`가 `ConfigManager`에 직접 값을 쓰도록 수정하십시오.
2.  **안전한 경로 처리**: `initializer.py`에서 `os.path.exists`와 문자열 f-string으로 경로를 조합하는 방식은 잠재적인 경로 조작(Path Traversal) 취약점을 가질 수 있습니다. `pathlib`을 사용하여 안전하게 경로를 결합하십시오. (예: `Path("config") / "scenarios" / f"{active_scenario_name}.json"`)

## 5. 🧠 Manual Update Proposal

- **Target File**: `design/TECHNICAL_DEBT.md` (또는 `design/manuals/TROUBLESHOOTING.md`)
- **Update Content**:
  ```markdown
  ## 자산 소멸 버그 (Zero-Sum Violation)

  - **현상 (Symptom)**: 시뮬레이션 실행 중 `MONEY_SUPPLY_CHECK`에서 총 통화량이 지속적으로 감소하며 음수 값에 도달. 기업/가계 청산(Liquidation) 로그에서 `Recovered: 0.00`과 함께 막대한 `Net Destruction` 값이 기록됨.
  - **원인 (Cause)**: 에이전트 청산 시, 해당 에이전트가 보유한 재고 및 자본 자산이 시장에서 현금화되지 않고 시스템에서 완전히 소멸되고 있음. 이는 총 통화량을 감소시켜 경제 시스템을 붕괴시킴.
  - **해결 (Solution)**: 청산 로직은 반드시 제로섬 원칙을 따라야 함. 모든 자산은 시장 매각, 상속, 채권자 분배 등을 통해 다른 경제 주체에게 이전되어야 하며, 임의로 소멸해서는 안 됨.
  - **교훈 (Lesson Learned)**: 시스템에서 에이전트를 제거하는 모든 로직은 반드시 자산 보존 법칙을 따라야 한다. 자산의 '소멸'은 신중하게 설계된 극히 예외적인 경우(예: 감가상각)에만 허용되어야 한다.
  ```

## 6. ✅ Verdict

**REJECT**

치명적인 자산 소멸 버그와 이번 PR의 핵심 기능인 시나리오 파라미터 시스템의 오작동은 시뮬레이션의 신뢰도를 심각하게 훼손합니다. 두 가지 Critical Issue를 우선적으로 해결한 후 다시 리뷰를 요청하십시오.
