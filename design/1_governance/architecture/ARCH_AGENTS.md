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

### 4.2 Facade-Component Pattern
- **Facade (Agent Class)**: 에이전트의 상태(State)와 정체성을 유지.
- **Component (Behavior Class)**: 실제 로직을 수행하는 **Stateless** 클래스들.
- **상태 전이**: Facade는 컴포넌트가 반환한 새로운 상태 DTO를 자신의 내부 변수에 재할당하여 상태를 확정합니다.

## 6. 핵심 원칙 및 교훈 (Economic Principles & Lessons)

### 6.1 에이전트 태생적 목적의 원칙 (Principle: Born with Purpose)
- **현상**: 새로 생성된 에이전트(Newborn)가 아무런 행동을 하지 않고 방치되다 결국 시스템에 의해 도태되는 현상 발생.
- **원인**: 에이전트 초기화 시 '욕구(Needs)' 사전이 비어 있어(`{}`), 의사결정 엔진이 해결해야 할 결핍을 인지하지 못함 (Apathy 상태).
- **해결**: 모든 신생 에이전트는 최소한의 생존 및 사회적 욕구(`NEWBORN_INITIAL_NEEDS`)를 부여받고 태어나야 함.
- **교훈**: 에이전트의 존재는 물리적 속성뿐만 아니라 **'내재적 동기(Intrinsic Motivation)'**가 주입될 때 비로소 완성됨. 목표가 없는 에이전트는 불활성 객체에 불과함.
