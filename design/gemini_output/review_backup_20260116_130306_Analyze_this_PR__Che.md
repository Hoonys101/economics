# 🔍 코드 리뷰 보고서: Firm 클래스 SoC 리팩토링

---

### 1. 🔍 Summary
`Firm` 클래스에 집중되어 있던 **생산(Production)** 및 **판매/마케팅(Sales)** 관련 로직을 각각 `ProductionDepartment`와 `SalesDepartment`라는 별도의 컴포넌트로 분리한 리팩토링입니다. 이 변경은 관심사의 분리(SoC) 원칙을 강화하여 코드의 모듈성과 테스트 용이성을 크게 향상시켰습니다. 또한, 신규 컴포넌트에 대한 단위 테스트가 추가되어 코드의 안정성을 보강했습니다.

### 2. 🚨 Critical Issues
- **하드코딩된 상수 (Magic Numbers)**: 설정 파일(`config_module`)로 관리되어야 할 여러 상수 값들이 코드 내에 직접 하드코딩되어 있습니다. 이는 향후 유지보수 및 밸런스 조정 작업을 어렵게 만듭니다.
    - `simulation/components/production_department.py` (L:26): 자동화 수준 감가율 `0.995`가 하드코딩되어 있습니다.
      ```python
      self.firm.automation_level *= 0.995 # Slow decay (0.5% per tick)
      ```
    - `simulation/components/sales_department.py` (L:73-75): 마케팅 예산 비율 조정 배율 `1.1`과 `0.9`가 하드코딩되어 있습니다.
      ```python
      self.firm.marketing_budget_rate = min(max_rate, self.firm.marketing_budget_rate * 1.1)
      ...
      self.firm.marketing_budget_rate = max(min_rate, self.firm.marketing_budget_rate * 0.9)
      ```
    - `simulation/firms.py` (L:632): 최소 마케팅 지출액 `10.0`과 지출을 위한 최소 자산 `100.0`이 하드코딩되어 있습니다.
      ```python
      if self.assets > 100.0:
          marketing_spend = max(10.0, self.finance.revenue_this_turn * self.marketing_budget_rate)
      ```

### 3. ⚠️ Logic & Spec Gaps
- 현재 분석된 Diff 내에서는 로직상 결함이나 Spec과의 불일치는 발견되지 않았습니다. 리팩토링의 의도대로 기능들이 각 컴포넌트로 잘 위임되었습니다.

### 4. 💡 Suggestions
- **상수 외부화**: 위에 언급된 모든 하드코딩된 값들을 `config_module`을 통해 주입받도록 수정하여, 중앙에서 쉽게 관리하고 조정할 수 있도록 개선해야 합니다.
- **스타일 가이드 준수**: `simulation/components/production_department.py`의 예외 처리 블록 내에 있는 `import traceback` 구문을 파일 상단으로 이동시켜 파이썬 스타일 가이드를 준수하는 것이 좋습니다.
  ```python
  # In production_department.py (L:104)
  except Exception as e:
      import traceback # <-- 이 줄을 파일 상단으로 이동
      logger.error(f'FIRM_CRASH_PREVENTED | Firm {self.firm.id}: {e}')
      logger.debug(traceback.format_exc())
      return 0.0
  ```

### 5. ✅ Verdict
**REQUEST CHANGES**

이번 리팩토링은 아키텍처 개선에 크게 기여하는 긍정적인 변경입니다. 다만, 여러 곳에 하드코딩된 상수 값들이 있어 프로젝트의 유지보수 표준을 위반합니다. 위에 지적된 Critical Issues (하드코딩)를 모두 수정하면 Approve 하겠습니다.
