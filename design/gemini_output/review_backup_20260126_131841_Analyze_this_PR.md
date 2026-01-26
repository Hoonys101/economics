# 🔍 Git Diff Review: `household-decision-engine-config`

---

### 1. 🔍 Summary
변경 사항의 핵심은 `ai_driven_household_engine`에 하드코딩되어 있던 '마법 숫자(magic number)' `0.05`를 `config.py`에 정의된 `DEFAULT_MORTGAGE_RATE`로 대체한 것입니다. 이 과정에서 household AI 관련 테스트 코드의 안정성도 개선되었습니다.

### 2. 🚨 Critical Issues
- 발견되지 않았습니다. 보안 및 데이터 무결성 관련 중대한 결함은 없습니다.

### 3. ⚠️ Logic & Spec Gaps
- **[INCONSISTENCY] 설정 값 접근 방식 불일치**: `simulation/decisions/ai_driven_household_engine.py` 파일 내에서 설정 값을 가져오는 방식이 두 가지로 혼용되고 있습니다.
    - **L70**: `nominal_rate = loan_market_data.get("interest_rate", config.default_mortgage_rate)`
        - `config` 모듈을 직접 `import` 하여 사용하는 방식입니다.
    - **L397**: `risk_free_rate = loan_market.get("interest_rate", getattr(self.config_module, "DEFAULT_MORTGAGE_RATE", 0.05))`
        - 클래스 생성 시 주입받은 `self.config_module` 객체를 사용하는 방식입니다.
    - 의존성 주입(Dependency Injection) 패턴을 따르는 `self.config_module` 사용이 테스트 용이성과 모듈화를 위해 권장됩니다. 코드 전체에서 일관된 패턴을 유지해야 합니다.

- **[REDUNDANCY] 하드코딩된 기본값 잔존**: L397의 `getattr` 함수에 기본값으로 `0.05`가 여전히 하드코딩되어 있습니다. 이는 마법 숫자를 제거하려는 원래의 목적과 일부 위배됩니다. 설정 값의 유일한 출처(Single Source of Truth)는 `config.py`가 되어야 합니다.

### 4. 💡 Suggestions
1.  **[REFACTOR] 설정 접근 통일**: L70의 `config.default_mortgage_rate`를 L397과 같이 `self.config_module.DEFAULT_MORTGAGE_RATE`를 사용하도록 수정하여 코드의 일관성을 확보하십시오.
2.  **[REFACTOR] 중복 기본값 제거**: L397의 `getattr`에서 하드코딩된 기본값 `0.05`를 제거하는 것을 고려하십시오. 엔진은 `config_module`이 항상 필요한 속성을 가지고 있다고 가정하는 것이 더 견고한 설계입니다.

### 5. 🧠 Manual Update Proposal
이번 변경은 "마법 숫자 금지"라는 중요한 개발 원칙을 잘 보여줍니다. 이를 프로젝트의 지식 베이스에 통합할 것을 제안합니다.

- **Target File**: `design/개발지침.md`
- **Update Content**:
  ```markdown
  ## 원칙: 매직 넘버 (Magic Numbers) 금지

  - **현상**: 소스 코드 내에 특별한 설명 없이 직접 사용된 숫자나 문자열 값. (예: `tax_rate = amount * 0.15`)
  - **문제점**:
    - 값의 의미를 즉시 파악하기 어렵다 (가독성 저하).
    - 값이 여러 곳에서 사용될 경우, 일관된 수정이 어렵고 잠재적 버그의 원인이 된다.
  - **해결책**:
    - 모든 상수는 `config.py`와 같은 중앙 설정 파일에 의미 있는 이름의 변수로 정의한다. (예: `CORPORATE_TAX_RATE = 0.15`)
    - 코드에서는 이 설정 변수를 직접 참조하거나, 의존성 주입(DI)을 통해 전달받아 사용한다.
  - **교훈**: 상수를 중앙에서 관리하면 코드의 가독성, 유지보수성, 재사용성이 크게 향상된다.
  ```

### 6. ✅ Verdict
**REQUEST CHANGES**

> 위에 제기된 `Logic & Spec Gaps` 항목들을 수정한 후 다시 리뷰를 요청해주십시오. 전반적인 방향은 훌륭하지만, 코드의 일관성과 견고함을 위해 추가 수정이 필요합니다.
