# 🔍 PR Review: Assets Refactor (Wallet API)

---

## 🔍 Summary

이 PR은 레거시 `agent.assets` (float) 속성 접근을 새로운 `Wallet` API 및 다중 통화를 지원하는 `Dict` 기반 자산 구조로 전환하는 중요한 리팩토링을 수행합니다. 하위 호환성을 보장하기 위해 안전한 자산 추출 로직을 여러 모듈에 걸쳐 적용했으며, 해당 변경 사항에 대한 명확한 인사이트 보고서를 포함하고 있습니다.

## 🚨 Critical Issues

**없음.** API 키, 외부 경로, 시스템 절대 경로 등 보안에 민감한 하드코딩은 발견되지 않았습니다.

## ⚠️ Logic & Spec Gaps

-   **[Hard-Fail] `simulation/systems/persistence_manager.py`의 리팩토링 불일치:**
    -   **현상:** 변경된 다른 모든 파일(`bank.py`, `system2_planner.py` 등)은 `wallet` 존재 여부, `assets`의 타입(dict/float)을 순차적으로 확인하는 안전한 하위 호환성 로직을 구현했습니다. 하지만 `persistence_manager.py`에서는 이 로직이 누락되었습니다.
    -   **기존 코드:**
        ```python
        total_assets = sum(h._econ_state.assets.get(DEFAULT_CURRENCY, 0.0) for h in simulation.households)
        ```
    -   **변경 후 코드:**
        ```python
        total_assets = sum(h.wallet.get_balance(DEFAULT_CURRENCY) for h in simulation.households)
        ```
    -   **문제점:** 이 코드는 시뮬레이션 내 모든 `household` 에이전트가 `.wallet` 속성을 가지고 있다고 가정합니다. 만약 레거시 에이전트나 `wallet`이 없는 다른 유형의 에이전트가 `simulation.households` 리스트에 포함될 경우, 즉시 `AttributeError`가 발생하여 시뮬레이션이 중단될 것입니다. 이는 다른 파일에서 일관되게 적용한 방어적 프로그래밍 원칙에 위배됩니다.

## 💡 Suggestions

-   **일관성 확보:** `simulation/systems/persistence_manager.py`의 자산 집계 로직을 다른 파일에서 사용된 것과 동일한 안전한 접근 방식으로 수정해야 합니다. 예를 들면 다음과 같습니다.

    ```python
    # 제안하는 수정안
    total_assets = 0.0
    for h in simulation.households:
        wealth = 0.0
        if hasattr(h, 'wallet'):
            wealth = h.wallet.get_balance(DEFAULT_CURRENCY)
        elif hasattr(h, 'assets') and isinstance(h.assets, dict): # 혹은 h._econ_state.assets
            wealth = h.assets.get(DEFAULT_CURRENCY, 0.0)
        elif hasattr(h, 'assets'):
            wealth = float(h.assets)
        total_assets += wealth
    ```

## 🧠 Manual Update Proposal

-   **Target File**: `communications/insights/AssetsRefactor.md`
-   **Review**: 제공된 인사이트 보고서는 훌륭합니다. `현상(Implicit Float Assumption) / 원인(Wallet introduction) / 해결(Safe asset extraction) / 교훈(Interface Enforcement)`의 구조를 잘 따르고 있으며, 기술 부채와 아키텍처 개선 방향을 명확하게 문서화했습니다. 이 PR의 요구사항을 완벽하게 충족합니다.

## ✅ Verdict

**REQUEST CHANGES (Hard-Fail)**

-   **사유:** `simulation/systems/persistence_manager.py`에 구현된 로직의 불일치로 인해 잠재적인 런타임 에러(`AttributeError`)가 발생할 수 있습니다. 이는 시스템 안정성을 해칠 수 있는 명백한 논리적 결함입니다. 인사이트 보고서 작성은 매우 훌륭했으나, 코드의 완전성이 우선되어야 합니다. 위에 제안된 대로 코드를 수정한 후 다시 리뷰를 요청해주십시오.
