# Atomic Firm Factory Specification (MISSION-PH35-SPEC-FIRM)

## 1. `modules/lifecycle/api.py` (API 초안)

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Any, Optional, Dict, runtime_checkable

# 기존 DTO 및 상수 재사용 (Purity 유지)
from modules.system.api import AgentID, CurrencyCode, DEFAULT_CURRENCY
from modules.finance.api import IFinancialAgent

@dataclass(frozen=True)
class FirmCreationRequestDTO:
    """
    기업 생성 요청을 캡슐화하는 순수 데이터 구조 (DTO).
    TD-FIN-FLOAT-INCURSION 방지를 위해 자본금은 반드시 int(Pennies)로 강제됩니다.
    """
    firm_type: str
    owner_id: AgentID  # 자본을 출자하는 주체 (Household, Public Manager, Central Bank 등)
    initial_capital_pennies: int
    config: Any  # FirmConfigDTO 객체
    currency: CurrencyCode = DEFAULT_CURRENCY

@dataclass(frozen=True)
class FirmCreationResultDTO:
    """
    원자적 기업 생성의 결과를 반환하는 DTO.
    """
    success: bool
    firm_id: Optional[AgentID]
    firm_instance: Optional[Any] # IFirm 프로토콜 준수 객체
    error_message: Optional[str]
    transaction_id: Optional[str] = None

@runtime_checkable
class IFirmFactory(Protocol):
    """
    기업 생성 라이프사이클을 관장하는 팩토리 인터페이스.
    TD-LIFECYCLE-GHOST-FIRM을 방지하기 위해 생성/등록/자본주입의 원자성을 보장합니다.
    """
    def create_firm_atomic(self, request: FirmCreationRequestDTO) -> FirmCreationResultDTO:
        """
        단일 트랜잭션 내에서 기업을 메모리에 할당, 레지스트리에 등록, 은행 계좌 개설, 초기 자본금을 주입합니다.
        실패 시 롤백(Zero-Sum 무결성 유지)합니다.
        """
        ...
```

---

## 2. `design/3_work_artifacts/specs/firm_factory_spec.md` (명세 초안)

### 2.1. Pre-Implementation Risk Analysis (아키텍처적 지뢰 분석)
- **God DTO (SimulationState) 의존성**: 팩토리가 `SimulationState`를 직접 주입받을 경우 결합도가 급증합니다. 팩토리는 `IAgentRegistry`, `ISettlementSystem`, `IAccountRegistry`와 같은 분리된 프로토콜에만 의존해야 합니다.
- **순환 참조 (Circular Imports)**: `Firm` 모듈과 `FirmFactory` 모듈이 서로를 참조하여 `ImportError`가 발생할 가능성이 높습니다. 의존성 주입 시 지연 로딩(Lazy Loading)을 사용하거나 인터페이스/타입 체킹 블록을 활용해야 합니다.
- **생성 중 실패로 인한 고스트 기업 (Ghost Firm)**: 자본 주입 전 레지스트리 등록을 완료하지 않아 `SettlementSystem`에서 계좌를 찾지 못하고 실패하는 `TD-LIFECYCLE-GHOST-FIRM`이 존재합니다. 트랜잭션 실패 시 할당된 ID와 레지스트리 등록을 완벽히 롤백하지 않으면 가비지 데이터가 쌓이게 됩니다.

### 2.2. 로직 단계 (Pseudo-code)
```text
class FirmFactory(IFirmFactory):
    dependencies:
        agent_registry: IAgentRegistry
        settlement_system: ISettlementSystem
        account_registry: IAccountRegistry

    function create_firm_atomic(request: FirmCreationRequestDTO) -> FirmCreationResultDTO:
        // 1. Validation
        if request.initial_capital_pennies < 0:
            return Result(success=False, error="Capital cannot be negative")

        // 2. Allocation
        firm_id = agent_registry.generate_next_agent_id()

        // 3. Instantiation (메모리상에 객체 생성)
        try:
            firm_instance = Firm(
                id=firm_id, 
                config=request.config, 
                firm_type=request.firm_type
            )
        except Exception as e:
            return Result(success=False, error="Instantiation failed")

        // 트랜잭션 롤백 추적을 위한 상태 플래그
        is_registered = False
        is_account_opened = False

        try:
            // 4. Registration (레지스트리 커밋)
            agent_registry.register(firm_instance)
            is_registered = True

            // 5. Banking (계좌 개설)
            // Bank ID가 별도로 지정되어야 하거나 디폴트 중앙은행/메인은행 연결
            bank_id = get_default_bank_id() 
            settlement_system.register_account(bank_id, firm_id)
            is_account_opened = True

            // 6. Capitalization (초기 자본 주입)
            transaction_record = None
            if request.initial_capital_pennies > 0:
                owner = agent_registry.get_agent(request.owner_id)
                if not owner:
                    raise RollbackException("Owner not found")

                // 투자자 -> 기업으로 자본 이동 (SSoT 원칙)
                transaction_record = settlement_system.transfer(
                    debit_agent=owner,
                    credit_agent=firm_instance,
                    amount=request.initial_capital_pennies,
                    memo="initial_capital_injection",
                    currency=request.currency
                )

                if transaction_record is None:
                    raise RollbackException("Capital transfer failed (Insufficient funds or Ledger error)")

            return Result(success=True, firm_id=firm_id, firm_instance=firm_instance, transaction_id=transaction_record.id)

        except Exception as rollback_trigger:
            // 7. Rollback Process
            if is_account_opened:
                settlement_system.deregister_account(bank_id, firm_id)
            if is_registered:
                // 내부적으로 inactive/dead 마킹 및 레지스트리 해제
                agent_registry.remove_or_deactivate(firm_id)
            
            return Result(success=False, error=str(rollback_trigger))
```

### 2.3. 예외 처리
- **RollbackException**: 자본 이체가 실패하거나 출자자를 찾지 못한 경우 명시적으로 발생시키며, 이 예외를 Catch하여 레지스트리에 임시 등록된 기업 객체를 파기하고 M2 오염을 차단합니다.
- **TypeError/ValueError (Float Incursion)**: 자본금이 `int`가 아닌 경우 조기에 예외를 발생시켜 `FloatIncursionError`를 사전에 방지합니다.

### 2.4. 인터페이스 명세 (DTO 필드 구조 요약)
- **`FirmCreationRequestDTO`**
  - `firm_type` (str): 산업 도메인 카테고리
  - `owner_id` (AgentID): 초기 자본을 출자할 모회사/개인/공공관리자의 식별자
  - `initial_capital_pennies` (int): 1센트 단위로 강제된 정수형 자본
  - `config` (Any/FirmConfigDTO): 기업 생성 설정 구조체
  - `currency` (CurrencyCode): 외환 지원을 위한 통화 코드 (기본: USD)

### 2.5. 🚨 [Conceptual Debt] (정합성 부채)
- **Context Triage: Ignore SimulationState Pass-Through**: 기존 테스트 코드나 모듈에서 `Firm(..., simulation_state=sim)` 형태로 God Class를 넘겨주던 패턴이 일부 남아있을 수 있습니다. 이는 새 아키텍처에서 Interface Segregation 원칙을 위반하므로, `IFirm` 구현 시 `ISettlementSystem` 등의 분리된 의존성만 주입받도록 우회하거나 리팩토링 대상으로 남겨둡니다. (Antigravity 검토 요망).
- **TD-WAVE3-DTO-SWAP**: `firm_type`은 궁극적으로 `IndustryDomain` Enum으로 대체되어야 하나, 본 미션에서는 기존의 `str`을 허용하는 구조적 부채를 허용합니다.

### 2.6. 검증 계획 (Testing & Verification Strategy)
- **New Test Cases**: 
  - **Happy Path**: 출자자의 자금이 팩토리를 통해 기업으로 원자적 이동을 완료하고 `FirmCreationResultDTO(success=True)` 반환을 검증 (`test_firm_factory_atomic_creation`).
  - **Edge Case (Rollback Check)**: 출자자의 잔고가 부족할 때 팩토리 메서드 호출 시 `success=False`를 반환하고, `IAgentRegistry`에 해당 기업 ID가 존재하지 않거나 Inactive 상태인지 검증.
- **Existing Test Impact**: 기존 유닛 테스트 중 `Firm`을 `SimulationState`와 함께 직접 인스턴스화하던 부분을 `MockFirmFactory`를 사용하는 구조로 변경해야 합니다.

### 2.7. Mocking 가이드
- **필수**: `tests/conftest.py`에 등록된 `golden_firms` 픽스처를 우선적으로 사용합니다.
- **사용법**: 
  ```python
  @pytest.fixture
  def mock_firm_factory():
      factory = MagicMock(spec=IFirmFactory)
      factory.create_firm_atomic.return_value = FirmCreationResultDTO(success=True, ...)
      return factory
  ```
- **금지**: `MagicMock(spec=SimulationState)`를 생성하여 공장으로 주입하는 행위를 절대 엄금합니다 (TD-TEST-MOCK-LEAK 방지). 팩토리에는 반드시 `IAgentRegistry` 등 격리된 의존성만 모킹하여 주입하십시오.

### 2.8. 🚨 Risk & Impact Audit (기술적 위험 분석)
- **DTO/DAO Interface Impact**: `FirmCreationRequestDTO` 도입 시 기존 `simulation/initialization/` 영역(e.g., `Bootstrapper`)의 기업 초기화 로직 수정이 반드시 병행되어야 합니다.
- **순환 참조 위험**: `FirmFactory`가 `Firm` 클래스를 직접 참조할 경우, 파일 구조에 따라 순환 참조 위험이 큽니다. `modules/lifecycle/firm_factory.py`와 같이 완전히 독립된 레이어에 배치하십시오.
- **설정 의존성**: 초기 자본금 설정값(`initial_capital_pennies`)이 `config.yaml`에 float(달러 기준)으로 남아있다면, 팩토리에 도달하기 전 설정 로더에서 `int`로 파싱되어야 합니다.

### 2.9. 🚨 Mandatory Reporting Verification
> **[Instruction to Implementation Team / Next LLM Session]**
> 반드시 위 설계 작업을 수행하거나 코드를 구현한 후, 분석 과정에서 발견된 인사이트와 기존 아키텍처 부채 연관성(`TD-LIFECYCLE-GHOST-FIRM`, `TD-FIN-FLOAT-INCURSION` 등)을 **`communications/insights/MISSION-PH35-SPEC-FIRM.md`** 고유 파일에 독립적으로 기록하십시오. 
> 
> 보고서에는 다음 세 가지가 필수 포함되어야 합니다:
> 1. [Architectural Insights]
> 2. [Regression Analysis] 
> 3. [Test Evidence] (pytest 통과 로그 복사본)
>
> 이 보고서가 누락될 경우 미션은 Hard-Fail 처리됩니다. 공용 파일인 `manual.md`에 병합하지 마십시오.