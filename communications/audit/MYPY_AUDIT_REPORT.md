# 📊 MYPY Static Analysis Audit Report

**Date**: 2026-02-24
**Scope**: `simulation/`, `modules/`
**Total Errors**: 832
**Target**: Full Type Safety & Penny Standard hardening.

---

## 🔍 1. Penny Standard Enforcement (Int vs Float)
가장 빈번한 오류로, 통화 관련 필드에 `float`이 전달되거나 산술 연산 시 `int` 타입 유실이 발생함.

- **주요 파일**: 
  - `modules/finance/central_bank/service.py` (target_cash_amount: float -> int)
  - `simulation/agents/central_bank.py` (Wallet add/subtract float -> int)
  - `simulation/systems/transaction_processor.py` (amount_settled float -> int)
  - `simulation/portfolio.py` (acquisition_price: float -> int)
- **해결 방안**: 모든 통화 관련 변수를 `int`로 강제 캐스팅하거나, DTO 정의를 `int`로 수정.

## 🧱 2. Protocol & DTO Drift
DTO 구조 변경 후 반영되지 않은 멤버 접근 및 프로토콜 불일치.

- **주요 파일**:
  - `simulation/policies/taylor_rule_policy.py` (GovernmentStateDTO attribute errors)
  - `modules/system/api.py` (IAgent name not defined)
  - `modules/system/services/command_service.py` (ISettlementSystem missing attributes)
- **해결 방안**: DTO 멤버 필드 최신화 및 프로토콜 인터페이스 확장.

## 🏗️ 3. Liskov Substitution Principle (Override)
상속 관계에서 메서드 시그니처가 부모와 불일치하여 발생하는 런타임 위험.

- **주요 파일**:
  - `modules/inventory/manager.py` (get_quantity, get_all_items 시그니처 불일치)
  - `simulation/bank.py` (grant_loan override 시그니처 불일치)
  - `simulation/agents/government.py` (decide 시그니처 불일치)
- **해결 방안**: 부모 클래스(Interface/Protocol)에 정의된 시그니처와 동일하게 맞추거나 `Any`를 활용한 유연한 시그니처 적용.

## 🧪 4. Initialization & Mocking Errors
테스트 및 초기화 시점에서 Mock 객체와 실제 타입 간의 비교 연산 오류.

- **주요 파일**:
  - `simulation/initialization/initializer.py` (MagicMock > int 비교 오류)
  - `modules/testing/utils.py` (Unannotated helper functions)
- **해결 방안**: 테스트 코드의 Mock 스펙 지정(`spec=...`) 강화 및 초기화 시점의 타입 가드 추가.

## 📉 5. Data Structure & Masking
`dict` 접근 시 키 타입 불일치(str vs int) 및 중복 정의.

- **주요 파일**:
  - `modules/finance/api.py` (Duplicate Error class definitions)
  - `simulation/markets/matching_engine.py` (Invalid index type for dict[int, ...])
- **해결 방안**: `AgentID`를 `int`로 통일하거나 사전 정의된 키 타입에 맞게 캐스팅.

---

## 🛠️ Implementation Strategy (Jules Missions)
본 리포트를 기반으로 Jules는 다음 순서로 모듈별 해결을 시도함:
1. **Foundation**: `modules/system`, `modules/common` (Root dependencies)
2. **Finance**: `modules/finance`, `simulation/finance` (Penny Standard)
3. **Simulation Core**: `simulation/orchestration`, `simulation/agents`
4. **Markets**: `simulation/markets`, `modules/market`
5. **Analytics**: `simulation/metrics`, `simulation/db`
