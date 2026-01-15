# 🏛️ 코드 리뷰 보고서: Sovereign Debt & Financial Credit (WO-072)

### 🔍 Summary

이 변경 사항은 새로운 `FinanceSystem` 모듈을 도입하여, 기존의 무상 보조금(Grant) 기반 구제금융을 이자부 대출(Senior Debt)로 전환하고, 재정 적자를 메우기 위한 국채(Sovereign Debt) 발행 시스템을 구현합니다. 또한 Altman Z-Score를 이용한 기업 지급 능력 평가 로직을 추가하여 '좀비 기업'을 식별합니다. 이는 하드코딩된 금융 규칙과 관련된 상당한 양의 기술 부채를 해결하는 중요한 아키텍처 개선입니다.

### 🚨 Critical Issues

- 발견되지 않았습니다. API 키, 시스템 절대 경로, 외부 저장소 URL 등의 하드코딩은 발견되지 않았습니다.

### ⚠️ Logic & Spec Gaps

1.  **[Minor] 국채 발행 실패 시 잠재적 오류**:
    *   **위치**: `simulation/agents/government.py` (`provide_household_support`, `invest_in_infrastructure` 등)
    *   **분석**: 정부는 자산이 부족할 경우 `self.finance_system.issue_treasury_bonds(needed, current_tick)`를 호출하여 자금을 조달합니다. 하지만 `issue_treasury_bonds` 함수는 시장에 구매 여력이 없을 경우 빈 리스트(`[]`)를 반환하며 채권 발행에 실패할 수 있습니다. 현재 정부 코드는 이 함수의 반환 값을 확인하지 않고, 자금이 성공적으로 조달되었다고 가정하고 다음 로직을 진행합니다. 이로 인해 정부의 자산이 실제로는 증가하지 않아, 해당 틱에서의 지출이 결국 실패하게 될 수 있습니다. 심각한 버그는 아니지만, 불필요한 연산과 잠재적 비효율을 유발합니다.

2.  **[Minor] 하드코딩된 구제금융 상환 비율**:
    *   **위치**: `modules/finance/system.py` (`grant_bailout_loan` 함수)
    *   **분석**: 구제금융 대출의 조건(Covenants)으로 `mandatory_repayment: 0.5`가 하드코딩되어 있습니다. 이는 기업이 이익을 낼 경우 이익의 50%를 의무적으로 상환해야 함을 의미합니다. 이 값은 중요한 정책 변수이므로, `config.py` 또는 정책 결정 시스템의 일부로 관리되어야 합니다.

### 💡 Suggestions

1.  **국채 발행 결과 확인**: `government.py`에서 `issue_treasury_bonds` 호출 후, 반환된 Bond 리스트가 비어있지 않은지 확인하여 자금 조달 성공 여부를 명시적으로 검증하는 로직을 추가하는 것을 권장합니다. 이는 시스템의 안정성을 높이고 디버깅을 용이하게 합니다.

    ```python
    # 제안 (government.py)
    if self.assets < effective_cost:
        needed = effective_cost - self.assets
        issued_bonds = self.finance_system.issue_treasury_bonds(needed, current_tick)
        if not issued_bonds:
            logger.warning(f"BOND_ISSUANCE_FAILED | Failed to raise {needed:.2f} for infrastructure.")
            return False # 지출 실패 처리
    ```

2.  **함수명 변경**: `simulation/components/finance_department.py`의 `distribute_dividends` 함수는 이제 배당금 분배뿐만 아니라 부채 상환 로직도 처리합니다. 함수의 책임이 확장되었으므로, `process_profit_distribution` 또는 `handle_repayments_and_dividends`와 같이 보다 명확한 이름으로 리팩토링하는 것을 고려해볼 수 있습니다.

3.  **SoC (관심사 분리) 개선**: `simulation/engine.py`에서 매 틱마다 `firm.age += 1`을 실행하는 로직이 추가되었습니다. 이는 `simulation/systems/demographic_manager.py`의 `process_aging` 함수와 역할이 유사하므로, 기업의 노화(Aging) 로직도 해당 시스템으로 통합하여 인구 통계 관련 로직을 한 곳에서 관리하는 것이 아키텍처의 일관성을 높일 것입니다.

### ✅ Verdict

**REQUEST CHANGES**

전반적으로 매우 훌륭한 아키텍처 개선이며, 프로젝트의 현실성을 크게 높이는 중요한 변경입니다. 위에 언급된 사소한 논리적 갭과 제안 사항들을 반영하면 시스템이 더욱 견고해질 것입니다. 개발자의 노고에 감사드립니다.
