# 🐙 Git Review: WO-116 Money Leak Fix Analysis

## 🔍 Summary

이 변경 사항은 시스템 내에서 발생하던 여러 화폐 생성 및 소멸(Money Leak/Creation) 버그를 수정하는 데 중점을 둡니다. 세금 징수를 화폐 파괴가 아닌 이전으로 처리하고, 대출 부도 처리 시 발생하는 대손상각을 명시적인 화폐 파괴로 기록하며, 자산 청산 과정에서 발생하는 암묵적인 화폐 생성을 추적함으로써 시스템의 Zero-Sum 원칙을 강화합니다.

## 🚨 Critical Issues

- **없음**. 보안 취약점이나 하드코딩된 경로는 발견되지 않았습니다.

## ⚠️ Logic & Spec Gaps

이 PR은 새로운 논리 결함을 도입하는 대신, 기존에 존재하던 심각한 Zero-Sum 위반 문제들을 해결합니다.

1.  **세금 처리 로직 수정 (`simulation/systems/tax_agency.py`)**
    *   **문제**: 이전에는 세금 징수 시 `government.total_money_destroyed`가 증가하여, 세금이 시스템에서 돈을 파괴하는 것으로 잘못 처리되었습니다.
    *   **수정**: 해당 라인을 제거하고, 주석(`Tax is Transfer, not Destruction`)을 통해 명확히 밝혔습니다. 이는 세금이 에이전트(가계/기업)에서 정부로 자산을 **이전**하는 행위라는 명세에 부합하는 올바른 수정입니다.

2.  **대출 부도 시 화폐 파괴 명시 (`simulation/bank.py`)**
    *   **문제**: 은행이 대출을 회수하지 못하고 대손상각(Write-off) 처리할 때, 해당 금액이 시스템에서 사라짐에도 불구하고 추적되지 않았습니다.
    *   **수정**: `process_default` 함수에서 대출 잔액(`loan.remaining_balance`)을 `government.total_money_destroyed`에 더해, 부도 처리로 인한 화폐 파괴를 명시적으로 기록합니다.

3.  **자산 청산 시 화폐 생성(연금술) 추적 (`simulation/systems/lifecycle_manager.py`)**
    *   **문제**: 기업이나 가계가 파산하여 재고(inventory)나 자본재(capital stock)를 청산할 때, `reflux_system.capture`가 해당 자산 가치를 화폐로 변환했지만, 이 과정이 화폐 발행(Issuance)으로 추적되지 않는 "연금술(Alchemy)" 버그가 있었습니다.
    *   **수정**: 청산된 자산 가치를 `state.government.total_money_issued`에 더하여, 이 과정이 명시적인 화폐 생성임을 기록하도록 수정했습니다.
    *   **추가 수정**: 기업 청산 시 주주 배분 로직에서 비활성 가계(inactive households)와 정부(government)를 포함시켜, 배분되어야 할 자산이 소실되지 않도록 수정했습니다.

## 💡 Suggestions

1.  **정부 에이전트 조회 방식 개선 (`simulation/bank.py`)**
    *   현재 `for a in agents_dict.values(): if a.__class__.__name__ == 'Government': ...` 와 같이 클래스의 문자열 이름에 의존하여 정부 에이전트를 찾고 있습니다. 이는 향후 리팩토링 시 오류를 유발할 수 있습니다. `state` 객체에 `state.government`와 같은 직접 참조 속성을 두거나, `state.get_agent_by_type('Government')` 같은 식별자를 통한 검색 메커니즘을 도입하는 것이 더 안정적일 것입니다.

2.  **캡슐화 검토 (`simulation/systems/lifecycle_manager.py`)**
    *   `AgentLifecycleManager`가 다른 에이전트의 `_add_assets`와 같은 보호된(protected) 메서드를 직접 호출하고 있습니다. 이는 객체의 캡슐화를 저해할 수 있는 아키텍처 패턴입니다. 해당 로직을 각 에이전트가 직접 처리하는 공개(public) 메서드로 노출하거나, 중앙 트랜잭션 시스템을 통해 처리하는 방안을 장기적으로 고려해볼 수 있습니다.

## ✅ Verdict

**APPROVE**

핵심적인 회계 버그를 정확히 식별하고 수정했으며, 시스템의 경제적 무결성을 크게 향상시키는 중요한 변경입니다. 제안된 사항은 마이너한 리팩토링 제안이므로, 즉시 반영하지 않더라도 머지하기에 충분합니다.
