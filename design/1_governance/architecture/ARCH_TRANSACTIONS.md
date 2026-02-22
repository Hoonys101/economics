# Architecture Detail: Transaction & Financial Integrity

## 1. 개요
본 시뮬레이션은 시스템 내의 화폐 및 자산이 무단으로 생성되거나 소실되지 않도록 하는 **제로섬(Zero-Sum)** 원칙을 아키텍처 수준에서 강제합니다. 모든 가치의 이동은 불변의 `Transaction` 객체를 통해 기록되고 처리됩니다.

## 2. 핵심 처리 원칙

### 2.1 Settlement System Mandate (결제 시스템 위임)
- 모든 에이전트 간 자산 이동은 반드시 중앙 `SettlementSystem`을 거쳐야 합니다.
- 직접적으로 에이전트의 balance를 수정하는 행위는 엄격히 금지됩니다.
- **원자적 강제(Atomic Force)**: 모든 자금 인출(Withdraw)과 입금(Deposit)은 원자적으로 처리되어야 하며, 입금 실패 시 반드시 인출된 자금을 롤백(Rollback)하여 화폐가 증발하지 않도록 보장합니다.
- **Batch Settlement & Escrow Pattern**: 복합적인 다자간 정산(예: 상품 거래 + 판매세) 또는 대규모 배치 정산 시, 모든 참여자의 조건이 충족될 때까지 자금을 가상의 결제 레이어(Escrow Matrix)에 예치한 후 일괄 분배합니다. 이는 개별 에이전트의 잔액 부족으로 인한 "부분적 성공(Partial Success)" 누출을 방지하며, 텐서 연산으로 넘어갈 때 정산 레이어의 병목을 제거합니다.
- **효과**: 원자성(Atomicity) 보장 및 전 시스템적 감사 추적(Audit Trail) 가능.

### 2.4 Settle-then-Record (결제 후 기록 원칙)
- 통계 업데이트(Money Issued, GDP 등) 및 원장 Commit은 반드시 `SettlementSystem`의 금융 결제가 성공한 **후**에만 수행되어야 합니다.
- 낙관적 업데이트(Optimistic Update)는 경제 내의 데이터 드리프트(Data Drift)와 제로섬 위반의 주요 원인이므로 금지됩니다.


### 2.2 Zero-Sum Distribution & Precision (Zero-Float Mandate)
- **Absolute Integer Core**: All financial modules, including M&A, Stock Market discovery, and Government budgeting, MUST operate in integer pennies. **No floats** are permitted at the settlement boundary.
- **Rounding Policy**: Any fractional calculation (interest, tax, premiums) must use explicit quantization (`round_to_pennies`) before transmission to the `SettlementSystem`.
- **나머지 처리**: N명에게 분배 시, N-1명에게는 `floor` 금액을 배분하고 마지막 1명에게 남은 모든 차액을 배분하여 시스템 내 총 통화량의 보존 법칙을 성립시킵니다.

### 2.3 Automatic Escheatment (귀속 원칙)
- 소유자가 불분명한 자산(파산한 기업의 잔여 자산, 처리되지 않은 벌금 등)은 임시 보관소(`Reflux Sink`)에 머물지 않고 즉시 국가(`Government`)로 귀속됩니다.

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

### 3.1 Specialized Transaction Handlers (전문 핸들러)
`TransactionManager`의 거대화(Bloating)를 방지하기 위해, 복잡한 비즈니스 로직이 필요한 트랜잭션 타입은 `modules/finance/transaction/handlers/`에 위치한 전용 핸들러로 위임됩니다.

- **GoodsTransactionHandler**: **Atomic Escrow Pattern**을 구현하여 상품 대금과 판매세의 원자적 정산을 보장합니다.
- **LaborTransactionHandler**: 소득세 귀착(Incidence) 로직을 관리하며, 고용주와 피고용인 간의 정산 및 세무 프로토콜을 집행합니다.
- **Saga Pattern**: 주거(Housing)와 같은 다단계 거래는 전용 Saga Handler를 통해 상태 전이의 무결성을 유지합니다.

## 4. 3단계 텐서 파이프라인 (Three-Phase Tensor Pipeline)
복잡한 상태 변경 및 대규모 병렬 처리를 위해 **의도(Think) -> 매칭(Match) -> 행동(Act)**의 3단계 파이프라인을 구축합니다.

1. **Phase 1: Intent Generation (의도의 벡터화)**:
   - 각 에이전트가 현재의 `WorldState` DTO를 읽어 `Intent` 벡터(예: 수요/공급량, 목표가)를 생성합니다.
   - 이 단계는 어떠한 상태 변화도 일으키지 않는 **순수 함수(Pure Function)** 연산이므로 100% 병렬 처리가 가능합니다.
2. **Phase 2: Market Clearing (시장 매개 정산)**:
   - 시장(Market)은 생성된 의도 벡터들을 거대한 매트릭스로 모아 교차(Clearing) 연산을 수행합니다.
   - 여기서 누가 누구에게 얼마를 주고 몇 개를 받을지를 나타내는 **"정산 매트릭스(Settlement Matrix)"**가 산출됩니다. 아직 에이전트 지갑은 변하지 않습니다.
3. **Phase 3: Deterministic State Update (행동의 확정)**:
   - 산출된 정산 매트릭스를 바탕으로 에이전트들의 지갑과 재고를 **일괄(Batch) 업데이트**합니다.
   - 시장이 이미 정산표를 확정했으므로 충돌(Contention)이나 롤백 리스크가 없는 결정론적(Deterministic) 업데이트가 가능합니다.

## 5. 아키텍처적 의의
이 구조는 시뮬레이션 내의 경제가 "가짜 돈"으로 돌아가는 것을 원천 봉쇄합니다. 모든 틱의 정산 결과는 수학적으로 완벽하게 추적 가능해야 하며, 이는 거시경제 시뮬레이션의 신뢰도를 결정하는 가장 중요한 기반입니다.

## 6. 에이전트 자산 정의 (Definition of Agent Assets)

금융 정합성의 명확성을 위해 에이전트의 '자산(Assets)'을 다음과 같이 엄격히 구분합니다. (Ref: TD-179)

1.  **현금 (Cash / M0)**: 에이전트가 직접 보유하고 있는 물리적 통화. `SettlementSystem.transfer`의 기본 대상입니다.
2.  **예금 (Deposits / M1-M2)**: 은행 장부에 기록된 디지털 통화. `IBankService`를 통해 관리됩니다.
3.  **지불 능력 (Spending Power)**: 에이전트가 즉시 동원 가능한 `Cash + Deposits`의 총합입니다.

## 7. 심리스 결제 프로토콜 (Seamless Payment Protocol)

에이전트의 유동성 흐름을 극대화하기 위해 다음 결제 로직을 강제합니다.

1.  **우선 순위**: 모든 거래 시 **현금(Cash)**을 사용합니다.
2.  **No Reflexive Liquidity (Budget Constraint)**: `SettlementSystem` strictly enforces `current_cash >= amount`. Automatic bank withdrawals are deprecated (LOD-121). 
3.  **Liquidity Bridge (The Escape Valve)**: To prevent systemic paralysis, agents MUST maintain an internal "Liquidity Bridge" handler that periodically transfers bank deposits to cash (via `bank.withdraw`) *before* settlement. This shifts the complexity from the core engine back to the agent's financial management.
4.  **정산 일관성**:
    -   구매자(Buyer)는 잔액 부족 시 결제에 실패하며, 이는 상위 모듈에서 `SolvencyException`으로 처리되어야 합니다.
    -   판매자(Seller)는 거래 대금을 현금으로 수취합니다.
5.  **효과**: "예산 없이는 집행 없다"는 원칙을 강제하여, 경제 내의 실제 유동성 압박과 신용 주기를 정확히 시뮬레이션합니다.
## 8. 통화량 회계 (Money Supply Accounting - M2)

시뮬레이션의 M2 통화량은 다음의 합으로 정의되며, 중복 합산을 엄격히 금지합니다.

1.  **시중 현금 (Currency in Circulation)**: 가계, 기업, 정부(중앙은행 제외)가 보유한 `agent.assets`.
2.  **은행 예금 (Bank Deposits)**: 은행 장부에 기록된 고객 부채 (`bank.deposits`).

**중복 방지 원칙 (Avoiding Phantom Liquidity):**
-   **대출 시**: 대출금은 현금으로 직접 지급되지 않고, 대출자의 **은행 예금** 계좌에 기입됩니다. 이때 M2는 예금 증가분만큼 상승하지만, 현금 유통량은 변하지 않습니다. (TD-178 해결)
-   **정산 시**: `SettlementSystem`은 현금을 우선 차감하고 부족 시 예금을 인출합니다. 이때 자금의 성격이 '예금'에서 '현금'으로 변환되거나 타인의 '현금'으로 이전되므로, 전체 M2(`Cash + Deposits`)는 보존됩니다.
-   **계산 공식**: `Total Money (M2) = sum(max(0, Agent Cashes)) + sum(Bank Deposits) + sum(min(0, Agent Cashes))`. 
-   **부채 처리 (Liability Rule)**: 에이전트의 마이너스 잔액(Overdraft)은 M2에서 단순 차감되는 '음의 자산'이 아니라, 은행 예금과 상쇄되는 **'부채(Liability)'**로 취급되어야 합니다. M2 Audit 시 음수 잔액은 자산 합산에서 제외하고 부채 계정에 별도 합산하여 가시성을 확보합니다.

## 10. 다중 통화 및 환전 정합성 (Multi-Currency & FX Integrity)

다중 통화 시스템 도입 시, 환율 변동으로 인한 통화량 증발 또는 무단 생성을 방지하기 위해 다음 원칙을 강제합니다.

### 10.1 "Barter Only" Exchange Pattern
- **원칙**: 환전은 단순한 수치 변환(`A * Rate = B`)이 아닌, **'물물교환(Barter)'** 트랜잭션으로 처리되어야 합니다.
- **방어 메커니즘**: `OrderBookMatchingEngine`을 통해 한 주체가 A 통화를 내놓고 다른 주체(또는 시장 조성자/중앙은행)가 B 통화의 정수(Penny)를 직접 교환해야 합니다.
- **효과**: 시스템 내 각 통화의 총량(M2)은 환율이 변하더라도 항상 보존(Conservation)됩니다.

### 10.2 Floating Point Leakage Defense
- 환율 계산 결과는 반드시 결제 프로토콜 진입 전 정수(Penny)로 양자화(Quantization)되어야 합니다.
- **Rounding Rule**: 모든 환전 잔여물은 버리지 않고 특정 계정(Exchange Buffer)에 귀속시켜 제로섬 무결성을 유지합니다.

## 9. Wallet Abstraction Layer (WAL) - 도입 예정

다중 통화(Multi-Currency) 체제하에서 `Dict[CurrencyCode, float]` 객체에 대한 직접 접근은 제로섬 위반과 데이터 드리프트의 주된 원인입니다. 이를 방지하기 위해 모든 에이전트는 날것의 자산 데이터 대신 `Wallet` 추상화 객체를 사용해야 합니다.

### 9.1 핵심 요구사항
1. **격리(Isolation)**: 에이전트는 자신의 자산 데이터(Dict)에 직접 쓰기 권한을 갖지 못하며, 오직 `Wallet` 인터페이스를 통해서만 값을 읽고 수정(제한적)할 수 있습니다.
2. **원자적 연산(Atomic Arithmetic)**: 자산의 가감은 반드시 원자적 메서드(`add`, `sub`)를 통하며, 이 메서드 내부에서 통화 유효성 검사 및 정산 처리가 수행됩니다.
3. **자동 감사(Auto-Audit)**: `Wallet` 내부에서 발생하는 모든 자산 변동은 글로벌 `MONEY_DELTA` 로그를 자동 생성하여 `trace_leak.py`가 즉각 감지할 수 있도록 합니다.
4. **연산자 오버로딩**: 에이전트 로직의 복잡성을 줄이기 위해, `Wallet` 객체 간 또는 `Wallet`과 `float` 간의 산술 연산을 지원하여 다중 통화 여부를 은택화(Encapsulation)합니다.
