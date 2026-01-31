# WORK ORDER:
**Subject**: Phase 8 Post-Implementation Tactical Cleanup
**From**: Antigravity (Chief Architect)
**To**: Jules (Lead Developer)
**Date**: 2026-01-02
**Status**: APPROVED

## 1. Context
Phase 8 (Adaptive Price Expectations) 구현이 완료되었습니다. 그러나 급격한 기능 추가로 인해 `config.py`의 가독성이 저하되었고, `core_agents.py`에 중복 로직과 노이즈성 로그가 잔존해 있다는 보고가 있었습니다. Phase 9 (M&A) 착수 전, 이를 정비해야 합니다.

## 2. Objectives
1. **Configuration Hygiene**: `config.py` 내 산재된 상수들을 Phase별(Basic, Gov, Brand, Inflation)로 헤더를 달아 그룹화하고 중복을 제거하십시오.
2. **Memory Structure Standardization**: `Household`와 `Firm` 등 모든 에이전트가 `self.memory` (Dict)를 통해 과거 상태를 저장하도록 `BaseAgent`에 표준 구조를 구현하십시오.
3. **Logic Integrity**: `core_agents.py`의 `update_perceived_prices` 메서드에서 발견된 '인플레이션 계산 로직 중복(Double Append)' 버그를 수정하십시오.
4. **Logging Optimization**: 1000틱 시뮬레이션을 대비하여, `DEBUG` 레벨로 내려야 할 고빈도 로그(`HOUSEHOLD_CONSUMPTION`, `PANIC_BUYING`)를 식별하고 조치하십시오.
4. **Enum Standardization**: `enums.py`에 `IMPULSIVE`, `CONSERVATIVE`를 정식 등록하고 코드 내 매핑 로직을 정규화하십시오.

## 3. Definition of Done (DoD)
- `config.py`가 Phase별로 섹션화되어야 함.
- `verify_inflation_psychology.py` 테스트가 'Logic Fix' 이후에도 통과해야 함.
- 불필요한 `INFO` 로그가 콘솔을 도배하지 않아야 함.

## 4. Special Instructions
- **No Big Refactor**: 구조를 뜯어고치는 과도한 최적화는 금지합니다. 위 항목만 "Surgical Strike"로 처리하십시오.
