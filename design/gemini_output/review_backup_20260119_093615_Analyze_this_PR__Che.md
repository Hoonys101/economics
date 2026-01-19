# 🔍 Code Review Report: Phase 28 Stress Testing

## 🔍 요약 (Summary)

본 변경점은 시뮬레이션에 `hyperinflation`, `deflation`, `supply_shock`과 같은 거시경제 스트레스 시나리오를 도입합니다. 가계(Household) 에이전트의 의사결정 로직에 인플레이션 기대 심리 가속화, 공황 매도(Panic Selling), 사재기(Hoarding), 부채 회피(Debt Aversion) 등의 행동 패턴이 추가되었습니다. 아키텍처 측면에서는 시나리오 설정을 담는 `StressScenarioConfig` DTO를 도입하고, 이에 대한 단위 테스트가 추가되었습니다.

## 🚨 중대한 이슈 (Critical Issues)

1.  **하드코딩된 경제 파라미터 (Hardcoded Economic Parameters)**
    *   **위치**: `simulation/core_agents.py` (Household), `simulation/decisions/ai_driven_household_engine.py`
    *   **문제**: 시뮬레이션의 핵심 로직을 결정하는 주요 경제 파라미터들이 코드 내에 직접 하드코딩되어 있습니다. 이 값들은 반드시 `config.py`나 `simulation.yaml` 같은 설정 파일에서 관리되어야 합니다.
        *   `PANIC_SELLING_ASSET_THRESHOLD`: `500.0` (core_agents.py, line ~850)
        *   Panic Sell Price (투매 가격): `0.1` (core_agents.py, line ~870)
        *   Debt Repayment Ratios: `0.5`, `1.1`, `0.9` (ai_driven_household_engine.py, line ~375)
        *   Default Inflation Rate: `0.02` (engine.py, line ~782)
    *   **영향**: 로직의 유연성을 저해하고, 값 변경을 위해 코드 수정이 필요하며, 보안 감사를 어렵게 만듭니다.

2.  **미사용 변수 및 중복 코드 (Unused Variable & Duplicate Code)**
    *   **위치**: `simulation/core_agents.py` (~line 860-872)
    *   **문제**: 공황 매도(Panic Selling) 로직에서 `sell_order` 변수가 선언되었으나 사용되지 않고, 바로 뒤에 거의 동일한 내용의 `stock_order`가 다시 선언되어 사용됩니다.
        ```python
        # sell_order는 선언 후 사용되지 않음
        sell_order = Order(...) 
        # stock_order가 sell_order를 덮어쓰는 형태로 중복 선언됨
        stock_order = Order(...) 
        orders.append(stock_order)
        ```
    *   **영향**: 명백한 버그 또는 코드 정리 누락으로, 의도치 않은 동작을 유발할 수 있습니다.

## ⚠️ 로직 및 명세 누락 (Logic & Spec Gaps)

1.  **핵심 로직에 대한 테스트 부재 (Missing Tests for Core Logic)**
    *   **문제**: `tests/phase28/test_stress_scenarios.py` 파일이 추가되었지만, 이벤트 발생(자산 증발, 현금 주입)에 대한 테스트만 존재합니다. 정작 이번 PR의 핵심인 아래의 신규 행동 경제 로직에 대한 단위 테스트가 **전혀 없습니다**.
        *   가계의 **공황 매도 (Panic Selling)** 로직
        *   AI의 **사재기 (Hoarding)** 로직
        *   AI의 **부채 회피 (Debt Aversion)** 및 우선 상환 로직
    *   **영향**: 핵심 기능이 의도대로 동작하는지 검증할 수 없으며, 향후 리팩토링 시 회귀(regression)를 방지할 수 없습니다.

2.  **불확실한 API 사용 (Uncertain API Usage)**
    *   **위치**: `simulation/core_agents.py` (~line 863)
    *   **문제**: 개발자가 남긴 주석은 `StockMarket`이 요구하는 `item_id` 형식에 대한 불확실성을 드러냅니다.
        ```python
        item_id=f"stock_{firm_id}", # StockMarket expects firm_id integer, but Order item_id string?
        ```
    *   **영향**: 해당 코드가 `StockMarket`의 API 명세와 일치하는지 확인되지 않았으므로, 런타임에서 주문이 실패할 가능성이 있습니다.

3.  **포트폴리오 관리 로직 건너뛰기 (Skipping Portfolio Management)**
    *   **위치**: `simulation/decisions/ai_driven_household_engine.py` (~line 390-398)
    *   **문제**: 부채 회피 모드(`is_debt_aversion_mode`)가 활성화되면, 부채 상환 주문만 생성하고 정기적인 포트폴리오 관리(`_manage_portfolio`) 로직 전체를 건너뜁니다.
    *   **영향**: 부채 상환을 위해 다른 자산(예: 주식)을 매각해야 할 수도 있는데, 이 로직이 완전히 배제되어 최적의 의사결정을 내리지 못할 수 있습니다. 포트폴리오 관리 로직을 건너뛰는 대신, 부채 상환을 최우선으로 고려하도록 조정하는 것이 더 바람직해 보입니다.

## 💡 제안 (Suggestions)

1.  **DTO 구조 리팩토링 칭찬**: `simulation/dtos/` 디렉토리를 생성하고 `api.py`와 `__init__.py`로 구조화한 것은 모듈의 책임을 명확히 하는 좋은 리팩토링입니다.
2.  **설정 로드 개선**: `simulation/decisions/action_proposal.py`에서 `config_module.get()`을 사용하여 설정값을 읽어오도록 변경한 것은 시스템의 유연성을 높이는 좋은 개선입니다. 다만, 하드코딩된 fallback 값 `["basic_food", "luxury_food"]`은 `config.py`에 상수로 정의하여 참조하는 것이 더 좋습니다.

## ✅ 판정 (Verdict)

**REQUEST CHANGES**

중대한 이슈(하드코딩, 버그)와 핵심 로직에 대한 테스트 부재는 머지(Merge)를 막는 심각한 결함입니다. 위 이슈들을 모두 수정한 후 다시 리뷰를 요청해주십시오.
