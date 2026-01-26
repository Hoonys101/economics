# 🔍 Git Diff Review: TD-115 & TD-111

---

## 🔍 Summary

This set of changes introduces crucial improvements for monitoring the simulation's monetary health. It establishes a `baseline_money_supply` at initialization to act as a canonical reference for detecting money creation or leaks (TD-115). Furthermore, it refines the money supply calculation by creating a new `get_m2_money_supply` metric that correctly excludes in-transit funds held by the `RefluxSystem`, thus fixing a perceived leak and providing a more accurate economic indicator (TD-111).

## 🚨 Critical Issues

None found. The changes appear safe and do not introduce any obvious security vulnerabilities or hardcoded secrets.

## ⚠️ Logic & Spec Gaps

None found. The implementation correctly distinguishes between the total money supply for integrity checks (`calculate_total_money`) and the effective money supply for economic reporting (`get_m2_money_supply`), which aligns with the specifications. The new test file provides solid verification for this logic.

## 💡 Suggestions

- **Test Brittleness**: In `tests/verify_td_115_111.py`, the final assertion uses a hardcoded value: `assert baseline == 101800.0`. This makes the test brittle; if initial conditions in the fixtures are changed, this test will fail. It would be more robust to calculate this expected value dynamically from the same fixtures used to create the simulation state.

  **Example:**
  ```python
  # In test_verify_td_115_and_111
  expected_baseline = sum(h.assets for h in households) + \
                      sum(f.assets for f in firms) + \
                      mock_config_module.INITIAL_BANK_ASSETS
  assert baseline == expected_baseline
  ```

## 🧠 Manual Update Proposal

-   **Target File**: `design/manuals/ECONOMIC_INSIGHTS.md`
-   **Update Content**: The core insight from this change is the critical distinction between different measures of the money supply. I propose adding the following section to the manual to capture this knowledge.

    ```markdown
    ---
    ## 통화량 측정: 회계적 총량(Integrity) vs 경제적 유효량(M2)

    **현상:**
    경제 주체(가계, 기업 등)의 자산 총합이 특정 틱에서 감소하여 '돈 유출(Leak)' 버그로 의심되는 상황이 발생했습니다. 하지만 중앙은행이나 외부 요인 없이 총량이 변하는 것은 시스템의 Zero-Sum 원칙에 위배됩니다.

    **원인:**
    자금 측정 로직이 '송금 중인 돈(In-transit Money)'을 고려하지 않았습니다. `RefluxSystem`에 일시적으로 보관된 자금은 아직 어떤 경제 주체에게도 귀속되지 않은 상태이지만, 전체 시스템의 총량에는 포함됩니다. 이 금액을 유효 통화량에서 제외하지 않아 착시가 발생했습니다.

    **해결:**
    두 가지 다른 목적의 통화량 측정 지표를 정의하고 분리했습니다.
    1.  **회계적 총량 (Integrity Check)**: `world_state.calculate_total_money()` - `RefluxSystem`을 포함한 시스템 내 모든 돈의 합. 이 값은 중앙은행의 개입 없이는 절대 변하지 않아야 하며, 시스템 무결성 검증에 사용됩니다.
    2.  **경제적 유효량 (M2 Money Supply)**: `tracker.get_m2_money_supply()` - `RefluxSystem`을 **제외**한, 실제 경제 주체들이 보유한 돈의 합. 이는 시장의 실질적인 유동성과 소비/투자 잠재력을 나타내는 지표로 경제 분석에 사용됩니다.

    **교훈:**
    - 시스템의 **회계적 무결성**을 위한 측정치와 **경제 분석**을 위한 측정치는 다를 수 있습니다.
    - '보이지 않는 돈'(e.g., in-transit)의 상태를 명확히 정의해야 정확한 경제 분석이 가능하며, 이를 통해 거짓 신호(False Signals)를 방지할 수 있습니다.
    ```

## ✅ Verdict

**REQUEST CHANGES**

The core logic is correct and well-implemented. However, please address the suggested improvement in the test file to remove the hardcoded value, which will increase the test's robustness and maintainability.
