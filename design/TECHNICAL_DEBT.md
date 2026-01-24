# 🛠️ Technical Debt Register

> **목적**: 시뮬레이션의 신뢰성을 저해하거나 유지보수를 어렵게 하는 기술적 부채를 추적 관리합니다.
> **원칙**: 모든 부채는 '해결 방안(Proposal)'과 '영향도(Impact)'가 명시되어야 합니다.

---

## 🚨 Critical (Must Fix Immediately)

### [TD-105] The Positive Drift Mystery (+320.0000)
- **등록일**: 2026-01-24
- **발견자**: Antigravity & User
- **증상**: 
    - `final_victory_check.log`에서 매 틱마다 `+320.0000`, `+292.4960` 등의 양수(+) 누수(Leak)가 지속적으로 관측됨.
    - 거래량과 무관하게 발생하는 것으로 보아, 시스템 내부 로직(이자 지급, 환류 분배 등)에서 발생하는 '의도치 않은 민팅(Minting)'으로 추정됨.
- **원인 가설**:
    1. `Bank.pay_interest`: 예금 이자를 지급할 때 은행 자산에서 차감하지 않고 허공에서 생성할 가능성.
    2. `RefluxSystem`: 잉여 자금을 분배할 때 부동 소수점 올림 처리 등으로 인해 실제 보유량보다 더 많은 금액을 뿌릴 가능성.
- **영향**:
    - 장기 실행 시 인플레이션 압력으로 작용.
    - "폐쇄 경제"라는 시뮬레이션의 대전제를 훼손하여 데이터 신뢰도 하락.
- **해결 방안**:
    - `Bank`와 `RefluxSystem`의 지출 로직을 전수 조사.
    - 만약 '이자'를 허공에서 생성하는 것이 의도라면, `Government.total_money_issued`에 기록하여 'Leak'이 아닌 'Minting'으로 잡히게 해야 함. (명확한 태깅 필요)

### [TD-106] Bankruptcy Liquidation Accounting
- **등록일**: 2026-01-24
- **증상**: 
    - 경제 불황 시(Tick 48, 52 등) `-30,000` 규모의 거대한 음수(-) 누수가 발생.
    - 이는 기업 파산 시 자산이 공중 분해되는 현상이지만, 장부에는 기록되지 않음.
- **원인**: `BankruptcyManager`가 기업을 제거할 때, 남은 자산을 `Government.total_money_destroyed`에 합산하지 않음.
- **해결 방안**:
    - 파산 처리 시 남은 자산을 0으로 초기화하기 직전에 `total_money_destroyed` 카운터를 업데이트.

---

## ⚠️ Major (Plan to Fix)

### [TD-104] Legacy Async Bond Fallback Removal
- **등록일**: 2026-01-24
- **내용**: `government.py` 등에 `issue_treasury_bonds_synchronous`가 실패할 경우를 대비한 옛날 비동기 코드(`transaction` 방식)가 남아있음.
- **조치**: 시스템 안정화 확인 후 해당 `else` 블록 삭제하여 코드 복잡도 감소.

---

## ℹ️ Minor (Monitor)

### [TD-107] CentralBank Asset Structure
- **내용**: `CentralBank`의 `assets`가 `float`가 아닌 `dict` 형태일 수 있다는 코드 흔적(`isinstance` 체크)이 발견됨. `IFinancialEntity` 인터페이스 통일 필요.
