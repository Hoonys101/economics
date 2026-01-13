# [SPEC CLARIFICATION] WO-057-C: The Actuator (Response to Jules Charlie)

Jules Charlie 요원의 정확한 지적에 대해 수석 아키텍트로서 다음과 같이 명확한 구현 지침을 하달합니다.

## 1. Action Space Mismatch 해결
- **원칙**: Spec(`phase24_smart_leviathan_spec.md`)이 Code(`government_ai.py`)보다 상위 권한을 가집니다.
- **지침**: 귀관(Charlie)은 `SmartLeviathanPolicy`에서 **5-Action (0~4)** 매핑 로직을 구현하십시오.
    - AI(Brain)가 아직 3-Action만 송출하더라도, Policy(Actuator)는 5-Action을 수용할 준비가 되어 있어야 합니다. (Jules Alpha가 Brain을 5-Action으로 업그레이드할 예정입니다.)
    - **Mapping**:
        - `0`: IR -0.25%p (Dovish)
        - `1`: Hold
        - `2`: IR +0.25%p (Hawkish)
        - `3`: Tax -1.0%p (Expansion)
        - `4`: Tax +1.0%p (Contraction)

## 2. Interest Rate Execution (Central Bank Link)
- **현황**: `Government` 에이전트는 `base_interest_rate`를 소유하지 않아 금리 조절이 불가능한 상태입니다.
- **해법**: `make_policy_decision` 메서드에 전달되는 `market_data` 딕셔너리를 활용하십시오.
    - `engine.py`는 `market_data["central_bank"]` 혹은 `market_data["loan_market"]`에 중앙은행 객체나 금리 제어 인터페이스를 노출해야 합니다.
    - 만약 직접 접근이 어렵다면, `Government` 에이전트가 `simulation.bank` (Commercial Bank)의 `base_rate`를 강제로 덮어쓰거나, `engine` 레벨에서 중앙은행에게 신호를 보내도록 수정해야 합니다.
- **Short-term Fix**: `Government` 클래스 내에 다음 로직을 추가하십시오.
    ```python
    # In Government.make_policy_decision
    if "central_bank" in market_data:
        cb = market_data["central_bank"]
        cb.base_rate = max(0.0, cb.base_rate + ir_delta)
    ```

## 3. Logging Standard
- **Format**: `POLICY_CHANGE | Mode: AI | Action: {Label} | IR: {Old}->{New} | Tax: {Old}->{New} | Reason: Inf={Inf:.1%}, Unemp={Unemp:.1%}`
- **Metrics**: `Inflation Rate`, `Unemployment Rate` 두 가지는 필수입니다.

---
**요약**: 귀관은 5-Action 매핑을 구현하고, `market_data`를 통해 중앙은행의 금리를 조작하는 코드를 `government.py`에 삽입하십시오. (권한 위임)
