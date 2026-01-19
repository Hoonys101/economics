# Technical Debt Report - TD-008: Advanced Finance System Upgrade

**Author:** Jules (Software Engineer)
**Date:** 2024-05-24
**Mission:** TD-008 Finance System Upgrade

---

## 1. 발견된 스파게티 코드 (Identified Spaghetti Code)
- **FinanceDepartment Logic Leaks**:
  기존의 `calculate_altman_z_score` 메서드가 `simulation/components/finance_department.py` (Agent Component) 내부에 구현되어 있었습니다.
  그러나 이 로직은 시스템 수준의 감사(`FinanceSystem.evaluate_solvency`)에서 사용되므로, 시스템이 에이전트의 내부 컴포넌트 메서드에 직접 의존하는 구조였습니다. 이는 "시스템이 규칙을 정하고 에이전트는 따른다"는 원칙을 흐리게 만듭니다.

## 2. 구현의 병목 (Implementation Bottlenecks)
- **Data Access & Encapsulation**:
  Z-Score 로직을 `modules/finance/domain`으로 분리했음에도 불구하고, 계산에 필요한 데이터(`retained_earnings`, `profit_history`)는 여전히 `FinanceDepartment`의 내부 상태로 관리됩니다.
  따라서 `FinanceSystem`이 이 데이터를 얻기 위해 `firm.finance.retained_earnings`와 같이 깊숙이 접근해야 하며, 이는 `FinanceDepartment`의 구현 변경에 `FinanceSystem`이 취약하게 만듭니다.

## 3. 신규 부채 (New Technical Debt)
- **Manual Data Extraction in System**:
  `FinanceSystem.evaluate_solvency` 메서드 내에서 `firm`과 `firm.finance`로부터 데이터를 수동으로 추출하여 `AltmanZScoreCalculator`에 주입하고 있습니다.
  ```python
  total_assets = firm.assets + firm.capital_stock + firm.get_inventory_value()
  working_capital = firm.assets - getattr(firm, 'total_debt', 0.0)
  retained_earnings = firm.finance.retained_earnings
  ```
  이러한 "Data Gathering" 코드는 중복될 가능성이 높고, `Firm`의 속성 이름이 바뀌면 `FinanceSystem`도 수정해야 하는 Coupling을 유지시킵니다.

## 4. 상환 권고 (Repayment Recommendations)
- **Standardized Financial Reporting**:
  `Firm` (또는 `FinanceDepartment`)이 `FinancialStatementDTO`를 반환하도록 리팩토링해야 합니다.
  `FinanceSystem`은 `firm.get_financial_statement()`를 호출하여 표준화된 데이터 객체를 받고, 이를 도메인 계산기에 넘기는 방식으로 변경하면 결합도를 낮출 수 있습니다.
- **Domain Service Usage**:
  `FinanceDepartment` 내부에서도 `AltmanZScoreCalculator`를 사용하도록 리팩토링하여 로직의 단일 진실 공급원(SSOT)을 유지해야 합니다. 현재는 `FinanceDepartment`에 구버전 로직이 남아있을 수 있습니다(이번 작업에서는 `system.py`만 수정함).
