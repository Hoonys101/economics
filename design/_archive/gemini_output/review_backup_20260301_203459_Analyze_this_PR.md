# 🔍 Summary
- 중앙은행 시스템(CentralBankSystem)에 글로벌 트랜잭션 리스트를 주입(Transaction Injection)하여 통화 발행/소각 시 누락되던(Ghost Money) 내역을 장부에 정상적으로 기록하도록 수정했습니다.
- `TickOrchestrator`의 `Phase_MonetaryProcessing`을 `Phase3_Transaction`으로 통합하여 트랜잭션 처리의 원자성과 동기화를 확보했습니다.
- M2 집계 시 `ID_PUBLIC_MANAGER`와 `ID_SYSTEM`을 제외하고, 채권 상환 시 원금(Principal)만 통화 수축으로 산정하도록 회계 로직을 정교화했습니다.

# 🚨 Critical Issues
- 발견된 심각한 보안 위반, 하드코딩, 혹은 제로섬(Zero-Sum) 파괴 버그가 없습니다. 결제 시스템(`SettlementSystem`)의 핵심 로직 우회 시도는 관찰되지 않았습니다.

# ⚠️ Logic & Spec Gaps
- `modules/government/components/monetary_ledger.py` 내부의 `process_transactions` 메서드에서 채권 원금을 추출할 때 `amount = float(repayment_details["principal"])`와 같이 부동소수점(Float)으로 캐스팅하고 있습니다.
  - 시스템 전반적으로 화폐 금액은 정수형(Integer)을 강제(`FloatIncursionError` 방지)하고 있으므로, 원장 통계의 정밀도 하락이나 부동소수점 오차 누적을 방지하기 위해 `int(repayment_details["principal"])`로 캐스팅하는 것이 아키텍처 원칙에 부합합니다.

# 💡 Suggestions
- `simulation/world_state.py`의 `calculate_total_money` 메서드 내 루프에서 매 에이전트마다 `str(holder.id)` 변환과 다중 분기문(`== str(...) or ...`)을 실행하고 있습니다. 
  - 성능 최적화를 위해 루프 진입 전 `SYSTEM_SINKS = {str(ID_CENTRAL_BANK), str(ID_PUBLIC_MANAGER), str(ID_SYSTEM)}`와 같이 집합(Set)을 미리 정의해 두고, 루프 안에서는 `if str(holder.id) in SYSTEM_SINKS:` 형식으로 검사하는 것을 권장합니다.
- `tests/unit/modules/government/components/test_monetary_ledger_expansion.py`에서 `tx.buyer_id = "4"`와 같이 매직 스트링을 사용했습니다. `ID_PUBLIC_MANAGER` 상수를 직접 임포트하여 사용하는 것이 유지보수에 좋습니다.

# 🧠 Implementation Insight Evaluation
- **Original Insight**: 
  > **WO-WAVE5-MONETARY-FIX: M2 Integrity & Audit Restoration**
  > 
  > 1. Ledger Synchronization via Transaction Injection
  > The root cause of the M2 leakage was identified as "ghost money" creation during implicit system operations, specifically Lender of Last Resort (LLR) injections. These operations used the SettlementSystem but failed to bubble up the resulting transactions to the WorldState transaction queue, which is the single source of truth for the MonetaryLedger. To fix this, we implemented a Transaction Injection Pattern for the CentralBankSystem.
  > 
  > 2. Orchestrator Phase Consolidation
  > We removed the redundant Phase_MonetaryProcessing from the TickOrchestrator...
  > 
  > 3. M2 Perimeter Harmonization
  > We refined the definition of M2 (Total Money Supply) in WorldState.calculate_total_money. The PublicManager (ID 4) and System Agent (ID 5) are now explicitly excluded from the M2 calculation...
  > 
  > 4. Bond Repayment Logic
  > We enhanced the MonetaryLedger to respect the split between Principal and Interest during bond repayments...
- **Reviewer Evaluation**: 
  - 훌륭한 인사이트 보고서입니다. M2 누수(Leakage)의 원인인 '고스트 머니' 현상을 정확히 진단하고, 트랜잭션 주입 패턴(Transaction Injection Pattern)을 통해 단일 진실 공급원(Single Source of Truth)을 유지한 점이 기술적으로 매우 타당합니다.
  - 특히 복잡한 오케스트레이터의 단계를 통합하여 경쟁 상태(Race Condition)를 예방하고, 통화 수축 산정 시 채권의 원금(Principal)과 이자(Interest)를 분리한 것은 현실의 거시경제 회계 원칙을 시뮬레이션에 훌륭하게 이식한 성과입니다.

# 📚 Manual Update Proposal (Draft)
- **Target File**: `design/2_operations/ledgers/ECONOMIC_INSIGHTS.md`
- **Draft Content**:
```markdown
### [WO-WAVE5] M2 누수 방지 및 트랜잭션 주입 패턴 (Transaction Injection Pattern)

*   **현상**: 중앙은행 시스템(Lender of Last Resort 등)에서 화폐 발행/소각 시, 글로벌 트랜잭션 큐에 해당 내역이 기록되지 않아 M2 지표와 실제 통화량 간의 불일치(Ghost Money)가 발생함.
*   **원인**: 암묵적 시스템 오퍼레이션이 `SettlementSystem`을 호출하여 잔고를 변경하지만, 발생한 트랜잭션을 `WorldState`의 글로벌 트랜잭션 큐로 끌어올리지(bubble up) 않음. 또한 `Phase_MonetaryProcessing`과 `Phase3_Transaction`이 분리되어 원장 기록 시점이 동기화되지 않음.
*   **해결**:
    1.  **트랜잭션 주입 패턴(Transaction Injection Pattern)**: `CentralBankSystem` 등 시스템 에이전트 초기화 시 `WorldState.transactions` 리스트 참조를 주입하여, 부수 효과(Side-effect)로 발생한 트랜잭션을 글로벌 원장에 직접 추가하도록 설계 변경.
    2.  **페이즈 통합**: `Phase_MonetaryProcessing`을 제거하고 모든 트랜잭션 처리와 원장 기록을 `Phase3_Transaction`으로 통합하여 원자적 실행을 보장함.
    3.  **M2 경계 명확화 및 상환 분리**: 시스템 성격의 주체(`ID_PUBLIC_MANAGER`, `ID_SYSTEM`)를 M2 집계에서 제외하고, 채권 상환 시 원금(Principal) 상환 부분만을 통화량 수축(Destruction)으로 산정하도록 회계 기준을 강화함.
*   **교훈**: 시스템 레벨에서의 자산 이동 내역도 반드시 일반 경제 주체와 동일하게 글로벌 트랜잭션 큐에 기록되어야 통계적 무결성이 유지됨. 회계 원장은 이자와 원금 상환 등 금융 이벤트의 세부 메타데이터에 기반하여 보다 정교하게 통화를 추적해야 함.
```

# ✅ Verdict
**APPROVE**