# 🐙 Git Diff Review: WO-146-monetary-policy

## 🔍 Summary
이번 변경은 테일러 준칙(Taylor Rule)에 기반한 새로운 `MonetaryPolicyManager`를 도입하여 중앙은행의 기준금리를 동적으로 결정하는 로직을 구현합니다. 또한, 기존에 하드코딩되어 있던 기업의 대출 금리 요청 로직을 시장 금리 기반으로 변경합니다. 전반적으로 통화 정책의 자동화 및 현실화를 목표로 하는 중요한 업데이트입니다.

## 🚨 Critical Issues
1.  **[CRITICAL BUG] `simulation/orchestration/phases.py` - `nominal_gdp` 항상 0으로 설정됨**
    - **위치**: `Phase0_PreSequence`의 `execute` 메소드 내 `MarketSnapshotDTO` 생성 부분
    - **문제**: `nominal_gdp`를 설정하는 코드 `nominal_gdp=latest_gdp if 'latest_gdp' in locals() else 0.0`에서, `latest_gdp` 변수가 해당 스코프 내에 정의되어 있지 않습니다. 이로 인해 `nominal_gdp`는 항상 `0.0`으로 설정되며, 이는 테일러 준칙 계산의 핵심 요소인 `output_gap`을 무의미하게 만들어 통화 정책 전체를 오작동시킵니다.
    - **영향**: 잘못된 기준금리가 계속해서 산출되어 경제 시뮬레이션의 안정성을 심각하게 해칩니다.

2.  **[HARDCODING] `simulation/decisions/firm/finance_manager.py` - 대출 금리 스프레드 하드코딩**
    - **위치**: `FinanceManager`의 `decide_borrowing` 메소드
    - **문제**: 기존의 `0.10` 하드코딩을 수정하였으나, 여전히 시장 금리가 없을 경우를 대비한 대체(fallback) 금리 `base_rate = 0.05`와, 가산금리(spread) `wtp_rate = base_rate + 0.05`가 새로운 매직넘버로 하드코딩되어 있습니다.
    - **영향**: 기업의 위험 프리미엄이나 시장 상황과 무관하게 고정된 값으로 대출을 시도하게 되어, 시장의 역동성을 저해합니다. 이 값들은 반드시 설정 파일(`config`)로 분리되어야 합니다.

## ⚠️ Logic & Spec Gaps
1.  **[SoC 위반/성능 저하] `simulation/orchestration/phases.py` - `MonetaryPolicyManager`의 비효율적 생성**
    - **위치**: `Phase0_PreSequence`의 `execute` 메소드 내부
    - **문제**: 매 시뮬레이션 틱(tick)마다 `mp_manager = MonetaryPolicyManager(state.config_module)` 코드를 통해 `MonetaryPolicyManager` 객체를 새로 생성하고 있습니다. 이 객체는 상태가 없으므로(stateless) 매번 새로 만들 필요가 전혀 없습니다.
    - **영향**: 불필요한 객체 생성으로 인해 매 틱마다 성능 저하를 유발합니다. 또한, 오케스트레이션 단계가 특정 구현체(`MonetaryPolicyManager`)에 직접 의존하게 되어 결합도가 높아지고 SoC(관심사 분리) 원칙을 위반합니다. 객체는 시뮬레이션 초기화 시점에 생성하여 주입(Dependency Injection)해야 합니다.

## 💡 Suggestions
1.  **`MonetaryPolicyManager` 주입(Injection)으로 리팩토링**
    - `State` 객체나 `Government` 객체 초기화 시점에 `MonetaryPolicyManager`를 생성하고, `Phase0_PreSequence`에서는 이를 참조하여 사용하도록 구조를 변경하여 결합도를 낮추고 성능을 개선하는 것을 제안합니다.

2.  **설정 파일(`config`)을 통한 대출 스프레드 관리**
    - `finance_manager.py`의 하드코딩된 `0.05` 값들을 `config/economy_params.yaml` 같은 설정 파일로 옮겨 `FIRM_LOAN_DEFAULT_RATE`, `FIRM_LOAN_RISK_PREMIUM` 등의 명확한 이름으로 관리해야 합니다.

## 🧠 Manual Update Proposal
이번 변경은 새로운 경제 모델(테일러 준칙)을 도입하는 중요한 업데이트이므로, 해당 지식을 프로젝트에 자산화해야 합니다.

-   **Target File**: `communications/insights/WO-146-Taylor-Rule-Monetary-Policy.md` (신규 생성 제안)
-   **Update Content**: 아래 템플릿에 맞춰 새 인사이트 보고서 작성을 제안합니다.

    ```markdown
    # Insight Report: WO-146 - Taylor Rule Monetary Policy

    ## 1. 현상 (Observation)
    - 기존 중앙은행의 기준금리 결정 로직이 정적(static)이거나 부재하여, 시장 상황에 대응하는 자동화된 통화 정책이 필요했다.
    - 기업의 대출 금리 결정 또한 하드코딩된 값에 의존하여 비현실적이었다.

    ## 2. 원인 (Cause)
    - WO-146 미션의 요구사항에 따라, 인플레이션과 실물 경제 성장(GDP)에 반응하는 동적 통화 정책 매커니즘을 구현해야 했다.

    ## 3. 해결 (Resolution)
    - `MonetaryPolicyManager` 모듈을 신규로 구현하여, 경제학에서 널리 사용되는 '테일러 준칙'을 기반으로 목표 기준금리를 계산하도록 하였다.
    - 계산식: `i_t = r* + pi_t + alpha * (pi_t - pi*) + beta * (log Y_t - log Y*)`
    - 사용된 파라미터(설정 파일에서 로드):
        - `CB_INFLATION_TARGET` (목표 인플레이션율)
        - `CB_TAYLOR_ALPHA` (인플레이션 갭에 대한 반응 계수)
        - `CB_TAYLOR_BETA` (생산량 갭에 대한 반응 계수)
        - `CB_NEUTRAL_RATE` (중립 실질 금리)
    - 이 계산 결과를 `CentralBank`의 `base_rate`에 매 틱마다 업데이트하여, 시뮬레이션 내 모든 금융 활동에 영향을 주도록 통합하였다.

    ## 4. 교훈 (Lesson Learned)
    - **핵심 로직의 변수 유효성 검증**: `phases.py`에서 `nominal_gdp`에 사용될 `latest_gdp` 변수가 존재하지 않아 정책이 오작동하는 치명적인 버그가 발생했다. 외부 데이터를 DTO로 변환할 때, 데이터의 존재 여부와 유효성을 반드시 검증해야 한다.
    - **SoC 및 의존성 주입**: Orchestration Layer에서 특정 컴포넌트를 직접 생성하는 것은 강한 결합을 유발하고 성능을 저하시킨다. 컴포넌트는 상위 레벨에서 생성하여 주입하는 방식이 확장성과 유지보수 측면에서 유리하다.
    - **매직넘버의 설정화**: `0.05`와 같은 상수는 의미를 파악하기 어렵고 변경이 어렵다. `FIRM_LOAN_RISK_PREMIUM`과 같이 명확한 이름으로 설정 파일에 정의하면 코드의 가독성과 유연성이 크게 향상된다.
    ```

## ✅ Verdict
**REQUEST CHANGES**

**사유:** `nominal_gdp`가 항상 0이 되는 치명적인 버그와 하드코딩된 매직넘버 문제를 해결해야 합니다. 또한 제안된 아키텍처 개선(의존성 주입)을 적용하는 것을 강력히 권고합니다.
