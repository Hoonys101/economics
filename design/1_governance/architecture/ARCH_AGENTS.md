I will update the `ARCH_AGENTS.md` file to accurately document the stateful component pattern used in the `Firm` agent. This involves replacing the existing "Facade-Component Pattern" section with a more detailed explanation that includes the trade-offs and risks identified in the pre-flight audit. This brings the architecture documentation in line with the actual implementation. I will now write the changes to the file `design/1_governance/architecture/ARCH_AGENTS.md`.
# Architecture Detail: Agent Dual-Structure & Value Systems

## 1. 개요
본 시뮬레이션의 에이전트는 단순히 규칙을 따르는 자동화된 객체가 아닙니다. 각 에이전트는 **근원적 가치관(Root Values)**을 가지고 있으며, 이를 달성하기 위해 **AI(강화학습)**와 **Rule-base(휴리스틱)**가 결합된 2중 구조로 동작합니다.

## 2. 에이전트별 근원적 가치관

| 에이전트 타입 | 근원적 가치관 (Core Value) | 이론적 배경 |
|---|---|---|
| **Household (가계)** | 생존 및 자아실현을 위한 욕구 충족 | **Maslow's Hierarchy of Needs** (생리적 욕구 -> 안전 -> 사회적 -> 존경 -> 자아실현) |
| **Firm (기업)** | 자산 축적 및 시장 지배력 강화 | **Profit Maximization** & Market Share Expansion |
| **Government (정부)** | 시스템 전체의 안정 및 후생 증대 | **Social Welfare Function** & Fiscal/Monetary Stability |
| **Bank (은행)** | 유동성 공급을 통한 금융 중개 수익 | **Fractional Reserve Banking** & Risk-Adjusted Returns |

## 3. 에이전트 2중 구조 (AI-Rule Hybrid)

에이전트의 의사결정은 추상적 방향 설정과 구체적 실행 수량 계산의 2단계로 나뉩니다.

### 3.1 방향성 설정 (AI Domain)
- **메커니즘**: Q-Learning 기반 강화학습.
- **역할**: 현재 시장 상황(`MarketSnapshotDTO`)을 보고 "공격적 투자", "보수적 소비" 등 **추상적 전략 방향(Aggressiveness Vector)**을 결정합니다.
- **학습**: 각 틱의 결과에 따라 근원적 가치관(예: 가계의 행복지수, 기업의 이윤)을 보상값(Reward)으로 활용하여 전략을 고도화합니다.

### 3.2 수량화 및 검증 (Rule-base Domain)
- **메커니즘**: 경제 이론 및 제약 조건 기반의 휴리스틱 로직.
- **역할**: AI가 결정한 방향성을 바탕으로, 실제 가용 자산 내에서 "얼마나 살 것인가?"와 같은 **구체적인 수치(`Order`)**를 계산합니다.
- **필터링**: 자산 범위를 벗어나는 무리한 행동을 차단하고, 시스템 내에서 유효한 형식을 갖춘 명령만 생성하도록 보장합니다.

## 4. 핵심 설계 패턴

### 4.1 Purity Gate (정보 순수성 게이트)
- 에이전트는 의사결정 시 라이브 시스템 객체에 직접 접근할 수 없습니다.
- 오직 불변의 **DTO(Data Transfer Object)** 형태의 월드 상태만을 입력받습니다.
- **효과**: 의사결정 과정에서의 Side-effect를 방지하고, 동일 상황에 대한 일관성 있는 행동을 보장합니다.

### 4.2 Facade-Component Pattern: A Pragmatic Shift to Stateful Components

This pattern, particularly in the `Firm` agent, has evolved from its original "stateless component" vision into a pragmatic, stateful architecture. This section documents the current, as-implemented state.

- **Facade (Agent Class)**: The `Firm` class acts as the central state-holding object for all its related business logic. It maintains the agent's identity and core state.
- **Stateful Components (Department Classes)**: Logic is encapsulated in `Department` classes (e.g., `HRDepartment`, `FinanceDepartment`). However, these are **stateful** components, not stateless helpers.
  - **Implementation**: Each component is initialized with a reference to the parent `Firm` instance (e.g., `self.hr = HRDepartment(self)`).
  - **Coupling**: This "parent pointer" pattern creates tight coupling, as components have unrestricted access to the `Firm`'s entire state and its other components (e.g., `self.parent.finance`).

#### Architectural Reality & Trade-offs
### 4.2 Stateless Engine & Orchestrator Pattern (New Standard)

To eliminate technical debt, circular dependencies, and hidden side effects, all agents (Household, Firm, Government) MUST follow the **Stateless Engine & Orchestrator Pattern**.

- **Orchestrator (The Agent Class)**: 
  - Acts as the sole **State Owner** and coordinator. 
  - Holds private DTOs (`bio_state`, `econ_state`, etc.).
  - Orchestrates the sequence of calls to various engines.
  - Applies state updates based on engine returns.
- **Stateless Engines (Pure Logic Components)**:
  - MUST NOT hold any internal state.
  - MUST NOT have references to the parent Agent instance.
  - MUST be pure functions: `(StateDTO, ContextDTO) -> ResultDTO`.
  - Input DTOs are treated as immutable within the engine.

#### Mandatory Design Rules (Guardrails):
1. **No Agent Handles**: Never pass `self` (the agent instance) to an engine. Pass only the data (DTO) the engine needs.
2. **Side-Effect Isolation**: Engines calculate; Orchestrators execute. An engine returns a `DecisionDTO` or `ActionDTO`; it never directly calls `market.place_order()` or `wallet.withdraw()`.
3. **Snapshot-Based Decisions**: All decision engines MUST use `HouseholdSnapshotDTO` or equivalent as the single source of truth for the agent's current state.
4. **Zero-Sum Enforcement**: Every fiscal/monetary transaction result must be balanced to zero.

This pattern is the non-negotiable standard for all refactoring sprints.

## 6. 핵심 원칙 및 교훈 (Economic Principles & Lessons)

### 6.1 에이전트 태생적 목적의 원칙 (Principle: Born with Purpose)
- **현상**: 새로 생성된 에이전트(Newborn)가 아무런 행동을 하지 않고 방치되다 결국 시스템에 의해 도태되는 현상 발생.
- **원인**: 에이전트 초기화 시 '욕구(Needs)' 사전이 비어 있어(`{}`), 의사결정 엔진이 해결해야 할 결핍을 인지하지 못함 (Apathy 상태).
- **해결**: 모든 신생 에이전트는 최소한의 생존 및 사회적 욕구(`NEWBORN_INITIAL_NEEDS`)를 부여받고 태어나야 함.
- **교훈**: 에이전트의 존재는 물리적 속성뿐만 아니라 **'내재적 동기(Intrinsic Motivation)'**가 주입될 때 비로소 완성됨. 목표가 없는 에이전트는 불활성 객체에 불과함.

### 6.2 수요 탄력성의 원칙 (Principle: Demand Elasticity - System 1 Physics)
- **현상**: 시장 자산과 재고가 충분함에도 불구하고, 에이전트들이 특정 가격 지점에서 구매를 일시에 중단하여 경제가 얼어붙는 'GDP 0' 데들락(TD-157) 발생.
- **원인**: 이진적(Buy/No-buy) 의사결정 구조와 시장 가격에 대응하지 않는 가격 경직성.
- **해결**: 가계의 수요를 불연속적인 단계가 아닌, 가격과 필요에 비례하는 **연속적인 수요 곡선(Continuous Demand Curve)**으로 모델링함.
- **교훈**: AI의 전략적 판단(System 2)은 물리 법칙과 같은 경제적 제약(System 1 Physics: Elasticity)과 결합될 때 비로소 예측 가능하고 안정적인 거시 경제를 형성함.
