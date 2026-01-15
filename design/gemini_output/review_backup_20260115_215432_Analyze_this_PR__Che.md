# 🏛️ Code Review: WO-072 Sovereign Debt & Financial Credit

## 🔍 Summary

이 PR은 시뮬레이션의 재정 시스템을 근본적으로 개편하여, 기존의 보조금(Grant) 기반 구제금융을 이자부 대출(Loan)로 전환하고, 정부의 재정 적자를 충당하기 위한 국채(Sovereign Debt) 발행 시스템을 도입합니다. 이는 "공짜 돈"을 제거하고 부채 기반의 현실적인 경제 모델로 나아가는 중요한 단계입니다. 새로운 `FinanceSystem` 모듈이 도입되었으며, 이에 따른 테스트 코드와 기술 부채 원장이 대규모로 업데이트되었습니다.

## 🚨 Critical Issues

**1. [Money Leak] 부채 상환 시 화폐 소멸 오류**
   - **위치**: `modules/finance/system.py`의 `service_debt` 함수
   - **분석**: 중앙은행(Central Bank)이 보유한 국채가 만기되어 정부가 원리금을 상환할 때, 정부의 자산(`government.assets`)은 `total_repayment`만큼 정상적으로 감소합니다. 하지만 이 상환된 돈이 **중앙은행의 자산으로 이전되지 않고 소멸합니다.** 코드는 중앙은행의 자산 목록에서 해당 채권(`bond`)을 제거할 뿐, 상환금을 수령하는 로직이 누락되었습니다. 이는 시스템의 총 통화량을 감소시키는 심각한 **'돈 복사'의 반대, 즉 '돈 소멸' 버그**입니다.
   - **코드**:
     ```python
     # in modules/finance/system.py, service_debt()
     if bond in self.central_bank.assets.get("bonds", []):
         # Central Bank gets the money back (e.g., QE unwind)
         self.central_bank.assets["bonds"].remove(bond) # <- 채권만 제거되고, 돈은 받지 않음 (CRITICAL BUG)
     else:
         # Assume the commercial bank holds it
         self.bank.assets += total_repayment # <- 은행은 정상적으로 상환금을 받음
     ```

## ⚠️ Logic & Spec Gaps

**1. [Incomplete QE Logic] 중앙은행 대차대조표 불일치**
   - **위치**: `modules/finance/system.py`의 `issue_treasury_bonds` 함수
   - **분석**: 중앙은행이 양적완화(QE)를 통해 채권을 매입할 때, 정부의 자산은 정상적으로 증가하여 화폐 창출이 이루어집니다. 중앙은행 또한 자산 목록에 채권을 추가합니다. 하지만 화폐를 창출한 주체인 중앙은행의 부채(Liability)가 기록되지 않아 대차대조표의 기본 원칙(자산 = 부채 + 자본)이 맞지 않습니다. 이는 기술 부채 `TD-037`에서 지적된 사항으로, 이번 PR에서 완전히 해결되지 않았습니다. 다만, QE의 본질을 구현하기 위한 중요한 첫 단계인 점은 긍정적입니다.

**2. [SoC Violation] 기업 연령 계산 위치**
   - **위치**: `simulation/engine.py`
   - **분석**: 기존에 `DemographicManager`가 기업의 나이를 계산하던 문제를 해결하기 위해, `simulation/engine.py`의 메인 루프에서 모든 기업의 나이를 증가시키는 로직(`firm.age += 1`)이 추가되었습니다. 이는 아키텍처적으로 이전보다 개선되었지만, 장기적으로는 `FirmManagementSystem`과 같은 별도의 시스템에서 처리하는 것이 관심사 분리(SoC) 원칙에 더 부합합니다. 현재는 허용 가능한 수준의 개선입니다.

## 💡 Suggestions

- **탁월한 기술 부채 관리**: `design/TECH_DEBT_LEDGER.md`를 매우 상세하고 정직하게 업데이트한 점이 인상적입니다. 이 PR이 어떤 기술 부채를 해결하고 어떤 새로운 부채를 발생시켰는지 명확히 추적하는 것은 프로젝트의 건강성을 유지하는 데 매우 중요합니다. 훌륭한 관행입니다.
- **견고해진 테스트 구조**: `conftest.py`를 도입하여 테스트 픽스처를 중앙화하고, 새로운 `FinanceSystem`에 대한 상세한 단위 테스트(`tests/modules/finance/test_system.py`)를 작성한 것은 매우 긍정적입니다. 이는 향후 리그레션 버그를 방지하는 데 큰 도움이 될 것입니다.

## ✅ Verdict

**REQUEST CHANGES**

'돈 소멸' 버그는 시뮬레이션의 통화량 보존 법칙을 위반하는 치명적인 결함입니다. 이 문제가 해결되기 전까지는 PR을 머지할 수 없습니다. `service_debt` 함수에서 중앙은행이 상환금을 정상적으로 수령(또는 의도에 따라 소각)하는 로직을 추가해야 합니다.
