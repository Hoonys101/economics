# 🔍 Git Diff 리뷰 보고서: TD-105 Investment Atomicity

---

### 1. 🔍 Summary
이번 변경은 시스템의 핵심 금융 컴포넌트인 `SettlementSystem`을 리팩토링하여 거래의 **원자성(Atomicity)**을 보장하는 데 중점을 둡니다. 불안정한 `try-except-rollback` 로직을 제거하고, 모든 거래 전에 자산을 먼저 검증하는 **'Check-then-Execute'** 패턴을 도입했습니다. 이로써 돈 복사 또는 자산 누수와 같은 치명적인 버그의 근본 원인을 해결하고 시스템의 재무 안정성을 크게 향상시켰습니다.

### 2. 🚨 Critical Issues
- 발견되지 않았습니다. 이전 구현에 존재하던 심각한 자산 불일치(Asset Drift) 가능성이 이번 변경을 통해 성공적으로 제거되었습니다.

### 3. ⚠️ Logic & Spec Gaps
- **`SettlementSystem.transfer`의 비정상 입력 처리**:
  - `amount <= 0`일 때, 경고를 기록하고 `True`를 반환합니다. 이는 거래가 성공적으로 "완료"(아무것도 하지 않음)되었다는 의미로 해석될 수 있으나, 호출자 입장에서는 혼란을 야기할 수 있습니다. 거래가 실행되지 않았으므로 `False`를 반환하여 "성공하지 않음"을 명시하는 것이 더 명확한 계약일 수 있습니다. 하지만 현재 구현이 치명적인 문제를 일으키지는 않습니다.

### 4. 💡 Suggestions
- **`FinanceDepartment` 내 중복 로직 리팩토링**:
  - `invest_in_automation`, `invest_in_rd`, `invest_in_capex` 세 메서드는 로직이 거의 동일합니다. 코드 중복을 줄이고 유지보수성을 높이기 위해, 이 로직을 하나의 내부 메서드로 추출하는 것을 강력히 권장합니다.
  - **예시:**
    ```python
    # In FinanceDepartment class
    def _make_investment(self, amount: float, reflux_system: Optional[Any], investment_type: str) -> bool:
        if self._cash < amount:
            return False

        if not (hasattr(self.firm, 'settlement_system') and self.firm.settlement_system and reflux_system):
            self.firm.logger.warning(f"INVESTMENT_BLOCKED | Missing SettlementSystem or RefluxSystem for {investment_type}.")
            return False

        transfer_success = self.firm.settlement_system.transfer(self.firm, reflux_system, amount, f"{investment_type} Investment")

        if not transfer_success:
            self.firm.logger.warning(f"{investment_type} investment of {amount:.2f} failed due to failed settlement transfer.")
            return False
        
        # R&D는 추가적인 로직이 있으므로 분기 처리
        if investment_type == "R&D":
            self.record_expense(amount)
            
        return True

    def invest_in_rd(self, amount: float, reflux_system: Optional[Any] = None) -> bool:
        return self._make_investment(amount, reflux_system, "R&D")

    def invest_in_capex(self, amount: float, reflux_system: Optional[Any] = None) -> bool:
        return self._make_investment(amount, reflux_system, "CAPEX")
    
    # ... etc
    ```

### 5. 🧠 Manual Update Proposal
이번 리팩토링은 금융 시스템 설계의 핵심 원칙을 보여주는 훌륭한 사례입니다.

- **Target File**: `design/manuals/TROUBLESHOOTING.md` (가정) 또는 유사한 개발 원칙/문제 해결 문서
- **Update Content**:
  ```markdown
  ---
  
  ### 현상 (Symptom)
  - 시스템의 총 자산(e.g., 화폐)이 이유 없이 증가하거나 감소하는 현상 (Asset Drift / Money Leak).
  - 특히, 여러 주체 간의 자산 이체(Transfer) 로직 실행 후 데이터 정합성이 깨지는 문제가 발생.
  
  ### 원인 (Cause)
  - 거래의 **원자성(Atomicity)**이 보장되지 않은 이체 로직.
  - `try-except-rollback` 구문을 사용한 수동 롤백은, 롤백 과정 자체에서 또 다른 실패가 발생할 경우 데이터 정합성을 깨트리고 자산 소실/생성을 유발함. (Ref: `SettlementSystem`의 과거 구현)
  
  ### 해결 (Solution)
  - **"사후 롤백(Post-Execution Rollback)"** 대신 **"사전 검증(Pre-Execution Check)"** 패턴을 적용.
  - 실제 자산을 변경하기 전에, 송금자의 자산이 충분한지, 조건이 모두 충족되는지 먼저 **검증(Check)**한다.
  - 모든 검증을 통과한 경우에만 **실행(Execute)**하며, 실행 단계는 실패 가능성이 없도록 최대한 단순하게 유지한다. 이체 로직은 `check-then-execute`의 단일 책임만 가지며, 롤백 책임을 갖지 않는다. (Ref: `SettlementSystem`의 신규 `transfer` 구현)
  
  ### 교훈 (Lesson)
  - 금융 시스템과 같이 데이터 정합성이 최우선인 로직에서 수동 롤백 구현은 매우 위험하며 지양해야 한다.
  - **상태 변경 전 모든 조건을 검증하여 실패 가능성을 원천 차단**하는 것이 훨씬 견고하고 예측 가능한 설계이다.
  ```

### 6. ✅ Verdict
**APPROVE**

핵심적인 아키텍처 문제를 해결한 훌륭한 변경입니다. 제안된 리팩토링은 후속 PR에서 처리하는 것을 권장합니다.
