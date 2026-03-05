### [TD-LIFECYCLE-GHOST-FIRM] Atomic Agent Lifecycle Initialization
* **현상 (Phenomenon)**: 에이전트(Firm) 생성 중 시스템(Settlement, Liquidity) 초기화에 실패할 경우, 레지스트리에는 등록되어 있으나 금융 기능이 동작하지 않는 'Ghost Firm'이 잔존하는 문제 발생. 추가적으로 `create_firm_mitosis` 과정에서 분할된 새 Firm 객체가 글로벌 레지스트리에 전혀 등록되지 않아 시스템이 해당 에이전트를 인식하지 못하는 치명적 누락 현상 발견.
* **원인 (Cause)**: `FirmFactory`가 `SimulationState`라는 God Object에 강하게 결합되어 있었으며, 객체 생성과 환경 등록(Bank Account 개설, Initial Liquidity 주입)이 Transaction(Atomic) 단위로 묶여 있지 않았음. 또한 에이전트 생성 도메인 분리 과정에서 fallback 로직이 `birth_context.households`에 firm을 추가하는 도메인 경계 침범 버그가 존재했음.
* **해결 (Solution)**:
    1. 생성 시 주입되는 컨텍스트를 `IBirthContext`와 `IFinanceTickContext`로 엄격히 분리하여 의존성을 통제함.
    2. 초기화 과정 실패 시 즉시 `RuntimeError`를 발생시키고 `firm.is_active = False`로 처리(Soft-Kill)하여 롤백 보장.
    3. Fallback 시 올바른 도메인 배열(`birth_context.firms`)로 등록하도록 수정하였고, Mitosis(`clone_firm`) 과정에도 `birth_context`를 주입하여 명시적으로 `agent_registry.register`를 호출하도록 보완.
* **교훈 (Lesson)**: 모든 Agent의 탄생(Birth)과 파생(Mitosis)은 부작용(Side-effect)을 동반하므로, 반드시 Atomic한 절차로 통제되어야 하며 God Object를 배제하고 명확한 Protocol Interface를 통해 Context를 주입받아야 함.
