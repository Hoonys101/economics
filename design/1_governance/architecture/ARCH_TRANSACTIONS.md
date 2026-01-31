# Architecture Detail: Transaction & Financial Integrity

## 1. 개요
본 시뮬레이션은 시스템 내의 화폐 및 자산이 무단으로 생성되거나 소실되지 않도록 하는 **제로섬(Zero-Sum)** 원칙을 아키텍처 수준에서 강제합니다. 모든 가치의 이동은 불변의 `Transaction` 객체를 통해 기록되고 처리됩니다.

## 2. 핵심 처리 원칙

### 2.1 Settlement System Mandate (결제 시스템 위임)
- 모든 에이전트 간 자산 이동은 반드시 중앙 `SettlementSystem`을 거쳐야 합니다.
- 직접적으로 에이전트의 balance를 수정하는 행위는 엄격히 금지됩니다.
- **원자적 강제(Atomic Force)**: 모든 자금 인출(Withdraw)과 입금(Deposit)은 원자적으로 처리되어야 하며, 입금 실패 시 반드시 인출된 자금을 롤백(Rollback)하여 화폐가 증발하지 않도록 보장합니다.
- **Atomic Escrow Pattern**: 복합적인 다자간 정산(예: 상품 거래 + 판매세) 시, 모든 참여자의 조건이 충족될 때까지 자금을 에스크로에 예치한 후 일괄 분배합니다. 이는 개별 에이전트의 잔액 부족으로 인한 "부분적 성공(Partial Success)" 누출을 방지합니다.
- **효과**: 원자성(Atomicity) 보장 및 전 시스템적 감사 추적(Audit Trail) 가능.

### 2.4 Settle-then-Record (결제 후 기록 원칙)
- 통계 업데이트(Money Issued, GDP 등) 및 원장 Commit은 반드시 `SettlementSystem`의 금융 결제가 성공한 **후**에만 수행되어야 합니다.
- 낙관적 업데이트(Optimistic Update)는 경제 내의 데이터 드리프트(Data Drift)와 제로섬 위반의 주요 원인이므로 금지됩니다.


### 2.2 Zero-Sum Distribution & Precision (제로섬 분배 및 정밀도)
- **정수 산술 기반**: 화폐 분배 시 부동 소수점 오차 누적을 원천 차단하기 위해, 내부적으로 정수(Cents 단위) 연산을 우선하거나 분배 후 잔액을 철저히 마지막 대상에게 귀속시킵니다.
- **나머지 처리**: N명에게 분배 시, N-1명에게는 `floor` 금액을 배분하고 마지막 1명에게 남은 모든 차액을 배분하여 시스템 내 총 통화량의 보존 법칙을 성립시킵니다.

### 2.3 Automatic Escheatment (귀속 원칙)
- 소유자가 불분명한 자산(파산한 기업의 잔여 자산, 처리되지 않은 벌금 등)은 임시 보관소(`Reflux Sink`)에 머물지 않고 즉시 국가(`Government`)로 귀속됩니다.
- **Anti-Pattern**: `EconomicRefluxSystem`과 같은 출처 불명의 자금 저장소 사용을 금지합니다.

## 3. 트랜잭션 처리 구조 (Pipeline Architecture)

단일 처리 방식에서 역할 분담이 명확한 파이프라인 구조로 설계되었습니다.

1. **TransactionManager (Orchestrator)**:
   - 트랜잭션 타입에 따라 적절한 하위 시스템으로 라우팅.
2. **SettlementSystem (Financial Layer)**:
   - 일반 자산 이동 처리 및 제로섬 원칙 강제.
3. **CentralBankSystem (Monetary Layer)**:
   - 화폐 발행(Minting) 및 소각(Burning) 등 특수 논제로섬(Non-Zero-Sum) 작업 수행.
4. **Registry & Accounting (State Commitment)**:
   - 비금융적 권리(재고, 소유권) 기록 및 금융 원장(수익/비용) 업데이트.

## 4. 2단계 상태 전이 (Two-Phase State Transition)
복잡한 상태 변경 시 **Plan(Phase 1)**과 **Finalize(Phase 3)**를 철저히 분리합니다.
1. **Plan**: 현재 상태를 읽어 `Intent` 혹은 `Transaction` 객체를 생성 (상태 변경 없음).
2. **Finalize**: 생성된 객체들을 일괄 처리하여 최종 상태 확정.

## 5. 아키텍처적 의의
이 구조는 시뮬레이션 내의 경제가 "가짜 돈"으로 돌아가는 것을 원천 봉쇄합니다. 모든 틱의 정산 결과는 수학적으로 완벽하게 추적 가능해야 하며, 이는 거시경제 시뮬레이션의 신뢰도를 결정하는 가장 중요한 기반입니다.
