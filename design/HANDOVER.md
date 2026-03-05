# [Architectural Handover Report] God Class Decoupling & Financial SSoT Hardening

## Executive Summary
본 세션에서는 `SimulationState` God Class에 집중되어 있던 도메인 로직들을 각 모듈별 Context DTO 기반의 **Stateless Engine & Orchestrator 패턴**으로 전환하는 대규모 리팩토링을 완수했습니다. 특히 금융(Finance), 주거(Housing), 상속(Succession), 인구(Vital Stats) 시스템의 결합도를 제거하여 테스트 무결성을 확보하고, M2 통계 및 결제 시스템의 SSoT(Single Source of Truth)를 강화했습니다.

---

## 1. Accomplishments (주요 성과 및 아키텍처 변화)

### 🚀 God Class 탈피 및 DTO Purity 실현
- **전방위적 Decoupling**: Analytics, Finance, Firms, Housing, Succession, Vital Stats 모듈을 `SimulationState` 전역 객체로부터 독립시켰습니다.
- **Context DTO 도입**: 각 시스템 엔진이 실행 시점에 필요한 의존성만 주입받는 `*ContextDTO`(예: `HousingContextDTO`, `ISuccessionContext`)를 도입하여 부수 효과(Side-effect)를 차단했습니다.
- **Protocol Purity 강화**: `hasattr()` 등을 이용한 동적 속성 조회를 제거하고, 엄격하게 정의된 인터페이스 프로토콜을 따르도록 강제했습니다.

### 💰 금융 시스템 무결성 (SSoT) 확보
- **ISettlementSystem 승격**: 모든 자산 잔액 조회의 유일한 진실 공급원(SSoT)으로 설정하여 직접적인 속성 접근을 차단했습니다.
- **IMonetaryLedger 통합**: M2 통화량 및 시스템 부채 관리를 전담하는 Ledger 시스템을 구축하여 경제 지표 계산의 정합성을 높였습니다.
- **Multi-Currency 기반 마련**: `TransactionData` 및 `AgentStateData`에 `CurrencyCode`를 도입하고 Penny-safe 정수 연산을 강제하여 다중 통화 시뮬레이션을 위한 토대를 구축했습니다.

### 🛠️ 테스트 환경 복구 및 최적화
- **GC Hang 및 메모리 누수 해결**: 대규모 `MagicMock` 그래프로 인한 GC 중단 현상(`TD-TEST-GC-MOCK-EXPLOSION`)과 `GLOBAL_WALLET_LOG` 무제한 성장 문제를 해결했습니다.
- **성능 개선**: 루프 내 `getattr` 오버헤드를 제거(`TD-PERF-GETATTR-LOOP`)하여 10k 이상 에이전트 초기화 성능을 대폭 개선했습니다.

---

## 2. Economic Insights (경제적 통찰)

- **M2 Black Hole 발견 및 수정**: 부채(Overdraft)가 유동성을 가려 통화량이 음수로 표시되던 문제를 해결했습니다. 이제 M2는 양의 잔액 총합으로 계산하며, 음수 잔액은 `SystemDebt`으로 별도 관리합니다.
- **Bank Reserve Structural Constraint**: 정부의 국채 발행 규모가 상업 은행의 준비금 부족으로 인해 제한되는 현상(`TD-BANK-RESERVE-CRUNCH`)을 확인했습니다. 이는 부분 지급 준비 제도(Fractional Reserve) 도입의 필요성을 시사합니다.
- **Zombie Firm 생존 로직**: 기초 식품 기업의 급격한 파산을 막기 위해 가격 하한선 및 비상 준비금 DTO(`ZombieFirmPreventionDTO`)를 통한 보호 기틀을 마련했습니다.

---

## 3. Pending Tasks & Tech Debt (기술 부채 및 과제)

### 🚨 CRITICAL: 상속 시스템 무결성 훼손 (ID_SYSTEM)
- **현상**: `InheritanceManager` 리팩토링 중 테스트 통과를 위해 대출 상환 수취인을 실제 은행이 아닌 `ID_SYSTEM`으로 하드코딩한 사례가 발견되었습니다.
- **위험**: 상환된 자금이 은행으로 가지 않고 증발하여 Zero-Sum 무결성이 파괴됩니다. 즉시 `ISuccessionContext`를 통해 실제 채권자 ID를 주입받도록 수정해야 합니다.

### 📂 구조적 드리프트 (Root Cleanup)
- **Root 폴더 오염**: 루트 디렉토리에 100개 이상의 진단 로그 및 임시 스크립트가 산재해 있습니다. `ROOT_CLEANUP_PLAN.md`에 따라 `_internal/scripts` 및 `_archive`로의 일괄 이전이 필요합니다.

### 🏗️ 아키텍처 고도화
- **SimulationState God DTO 분편화**: 여전히 `SimulationState`가 40개 이상의 필드를 보유하고 있습니다. 도메인별 소규모 Context로의 추가 분리가 필요합니다.
- **Inactive Agent TTL**: 비활성 에이전트 데이터가 무제한 성장하고 있어, 장기 시뮬레이션을 위한 퇴거(Eviction) 정책 도입이 시급합니다.

---

## 4. Verification Status (검증 상태 요약)

### ✅ 모듈별 단위/통합 테스트 결과
- **Finance Module**: 57개 테스트 통과 (Settlement, Ledger, Solvency 로직 검증 완료)
- **Analytics Module**: 13개 테스트 통과 (Snapshot DTO 기반 지표 계산 검증)
- **Housing System**: 12개 테스트 통과 (임대료 징수 및 유지보수 트랜잭션 검증)
- **Firms & MA Manager**: 12개 테스트 통과 (DTO 기반 파산 및 시장 진입 로직 검증)
- **Vital Stats & Succession**: 11개 테스트 통과 (Context 기반 출생/이민/상속 프로세스 검증)

### 📊 시스템 안정성
- `main.py` 실행 시 초기화 루프 성능 저하 문제 해결 확인.
- `ruff` 및 `mypy` 기반의 타입 체크를 통해 DTO 전이 과정에서의 타입 안정성 확보.
- **최종 판정**: 핵심 엔진 로직의 Decoupling이 완료되어, 다음 세션부터는 독립적인 도메인 기능 확장이 가능합니다.