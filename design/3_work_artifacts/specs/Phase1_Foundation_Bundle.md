# 🖋️ Specification Draft: FOUND-01 GlobalRegistry & Migration

**Status**: Draft (Scribe)  
**Ref Version**: v1.0.0 (2026-02-13)  
**Mission Key**: FOUND-01-REGISTRY  
**Target File**: `modules/system/registry.py`

---

## 1. Overview
기존 `config.py` 및 YAML에 고정되었던 파라미터들을 런타임에 동적으로 수정하고 관리하기 위한 `GlobalRegistry`를 설계합니다. 이는 God-Mode의 실시간 조작을 위한 데이터 기반(Foundational) 미션입니다.

---

## 2. API Outline (`modules/system/registry.py`)

```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

class OriginType(IntEnum):
    SYSTEM = 0   # 엔진 기본값
    CONFIG = 1   # YAML 파일 로드 값
    GOD_MODE = 2 # 관찰자 직접 개입 (Highest Priority, Forced Lock)

@dataclass
class RegistryValueDTO:
    key: str
    value: Any
    domain: str
    is_locked: bool = False
    origin: OriginType = OriginType.SYSTEM
    metadata: Dict[str, Any] = field(default_factory=dict)

class GlobalRegistry:
    """
    엔진의 모든 거시/미시 파라미터를 중앙에서 관리하는 저장소.
    Singleton이 아니며 Simulation 컨테이너에 의해 주입됨.
    """
    def __init__(self, initial_data: Optional[Dict] = None):
        self._store: Dict[str, Dict[str, RegistryValueDTO]] = {}
        if initial_data:
            self.migrate_from_dict(initial_data)

    def get(self, domain: str, key: str, default: Any = None) -> Any:
        """파라미터 조회. 존재하지 않을 경우 default 반환."""
        ...

    def update(self, domain: str, key: str, value: Any, source: RegistrySource = RegistrySource.SYSTEM):
        """
        파라미터 업데이트. 
        만약 'GOD'에 의해 Lock이 걸린 경우 'SYSTEM' 소스의 업데이트는 거부됨.
        """
        ...

    def lock(self, domain: str, key: str):
        """God-Mode 조작 시 엔진 내부 로직이 덮어쓰지 못하도록 고정."""
        ...

    def unlock(self, domain: str, key: str):
        ...

    def migrate_from_dict(self, data: Dict[str, Any]):
        """YAML/Config 딕셔너리를 레지스트리 구조로 마이그레이션."""
        ...
```

---

## 3. Logic & Pseudo-code

### 3.1 Update Logic with Ownership Lock
```python
def update(self, domain, key, value, source):
    target = self._store.get(domain, {}).get(key)
    
    if target and target.is_locked and source == RegistrySource.SYSTEM:
        # God-Mode가 고정한 변수는 엔진이 건드릴 수 없음
        logging.info(f"Update rejected: {domain}.{key} is locked by GOD.")
        return False
    
    # 값 업데이트 및 소스 기록
    new_entry = RegistryValueDTO(key=key, value=value, domain=domain, source=source)
    if source == RegistrySource.GOD:
        new_entry.is_locked = True # God 조작 시 자동 Lock
        
    self._store.setdefault(domain, {})[key] = new_entry
    return True
```

---

## 4. Risk & Impact Audit (기술적 위험 분석)

- **순환 참조 위험**: `GlobalRegistry`는 최하단 `system` 모듈에 위치해야 하며, `config`나 `utils` 외의 다른 도메인을 임포트해서는 안 됩니다.
- **테스트 영향도**: `from config import PARAM` 형식을 사용하는 기존 코드들은 `Registry.get()` 호출 방식으로 리팩토링이 필요합니다. 리팩토링 전까지는 `config.py`가 Registry의 Wrapper 역할을 수행하도록 Bridge를 설계해야 합니다.
- **성능 저하**: 매 틱 수천 번 호출되는 루프 내에서의 딕셔너리 조회 오버헤드를 방지하기 위해, 자주 사용되는 값은 `Registry.subscribe()`를 통한 로컬 캐싱 전략이 필요할 수 있습니다.

---

## 5. Testing & Verification Strategy

- **Happy Path**: `GOD` 소스로 파라미터 수정 후 `SYSTEM` 소스의 수정이 차단되는지 확인.
- **Migration Test**: `economy_params.yaml`을 로드하여 Registry의 초기 상태가 기존 설정과 일치하는지 검증.
- **Integration Check**: `ProductionEngine`의 생산 계수를 Registry로 교체한 후, 시뮬레이션 중 실시간으로 생산량이 변하는지 확인.

---

## 6. Mandatory Reporting Verification
본 설계 과정에서 발견된 기술 부채(예: 하드코딩된 설정 파일의 산재)와 인사이트를 `communications/insights/FOUND-01-REGISTRY.md`에 기록하였습니다.

---
---

# 🖋️ Specification Draft: FOUND-02 Government Decomposition

**Status**: Draft (Scribe)  
**Ref Version**: v1.0.0 (2026-02-13)  
**Mission Key**: FOUND-02-GOV-DECOMP  
**Target File**: `modules/government/services/*.py`

---

## 1. Overview
TD-226~229 해결을 위해 거대해진 `Government` 클래스를 `TaxService`, `WelfareService`, `BondService`로 분해합니다. 각 서비스는 독립적인 로직을 가지며, `SettlementSystem`을 통해서만 자금을 이동시킵니다.

---

## 2. API Outline (`modules/government/api.py`)

```python
from typing import Protocol, List
from core.dtos import TransactionDTO

class GovernmentService(Protocol):
    def process_tick(self, context: dict) -> List[TransactionDTO]:
        """매 틱마다 수행할 로직과 그에 따른 트랜잭션 목록 반환."""
        ...

class TaxService:
    def calculate_income_tax(self, agents: List[Any]) -> List[TransactionDTO]:
        ...

class WelfareService:
    def distribute_subsidies(self, needy_agents: List[Any]) -> List[TransactionDTO]:
        ...

class GovernmentOrchestrator:
    """기존 Government 클래스를 대체하는 오케스트레이터."""
    def __init__(self, services: List[GovernmentService], settlement_system: Any):
        self.services = services
        self.settlement = settlement_system

    def run_fiscal_policy(self):
        # 모든 서비스의 트랜잭션을 수집하여 SettlementSystem에 일괄 제출
        ...
```

---

## 3. Logic & Pseudo-code

### 3.1 Transaction-Based Execution
```python
def run_fiscal_policy(self):
    all_transactions = []
    for service in self.services:
        txs = service.process_tick(self.get_current_context())
        all_transactions.extend(txs)
    
    # 원자적 트랜잭션 집행
    success, failure_reason = self.settlement.execute_batch(all_transactions)
    if not success:
        self.handle_fiscal_failure(failure_reason)
```

---

## 4. Risk & Impact Audit (기술적 위험 분석)

- **Government God Class 분해**: 기존 `Government`가 가진 상태(예: `current_reserve`)를 어느 서비스가 소유할지 명확히 해야 합니다. `TreasuryDAO`를 신설하여 공통 자산 상태를 관리하는 것이 권장됩니다.
- **순환 참조**: `TaxService`가 에이전트 리스트를 조회할 때 `HouseholdModule`을 직접 참조하지 않도록 `AgentRegistry`나 `DTO` 리스트를 전달받아야 합니다.
- **Zero-Sum Integrity**: 세금 징수와 복지 지출의 총합이 정부 계좌의 잔고와 일치하는지 매 틱 `Audit`이 필요합니다.

---

## 5. Testing & Verification Strategy

- **Mocking 가이드**: `tests/conftest.py`의 `golden_households`를 사용하여 세금 계산 로직이 정확한 `TransactionDTO`를 생성하는지 검증.
- **Integrity Check**: `WelfareService`가 정부 잔고보다 많은 금액을 지불하려 할 때 `SettlementSystem`에서 거부되는지 확인.

---

## 6. Mandatory Reporting Verification
본 서비스 분해 과정에서 식별된 정부 로직의 복잡성과 리팩토링 제안을 `communications/insights/FOUND-02-GOV-DECOMP.md`에 기록하였습니다.

---
---

# 🖋️ Specification Draft: FOUND-03 Sacred Sequence Phase 0 Intercept

**Status**: Draft (Scribe)  
**Ref Version**: v1.0.0 (2026-02-13)  
**Mission Key**: FOUND-03-INTERCEPT  
**Target File**: `modules/system/scheduler.py`

---

## 1. Overview
시뮬레이션 인과율을 보존하면서 외부 명령(God-Mode)을 안전하게 주입하기 위해, 'Sacred Sequence'의 최전방에 `Phase 0 (Intercept)` 단계를 추가합니다.

---

## 2. API Outline (`modules/system/scheduler.py`)

```python
from simulation.dtos.commands import GodCommandDTO

class TickScheduler:
    def __init__(self):
        self.command_queue: List[GodCommandDTO] = []
        self.registry: GlobalRegistry = ...
        self.settlement: SettlementSystem = ...

    def queue_command(self, cmd: GodCommandDTO):
        """외부(WebSocket/Dashboard)에서 명령 인입 지점."""
        self.command_queue.append(cmd)

    def _phase_0_intercept(self):
        """
        Phase 1 시작 전 모든 외부 조작 명령을 처리.
        """
        ...

    def run_tick(self):
        self._phase_0_intercept()  # 신설
        self._phase_1_perception()
        self._phase_2_contract()
        # ... 중략 ...
        self._phase_8_settlement_and_audit()
```

---

## 3. Logic & Pseudo-code

### 3.1 Command Consumption Logic
```python
def _phase_0_intercept(self):
    while self.command_queue:
        cmd = self.command_queue.pop(0)
        try:
            if cmd.command_type == "SET_PARAM":
                # FOUND-01의 Registry 업데이트 호출
                self.registry.set(
                    cmd.target_domain, 
                    cmd.parameter_name, 
                    cmd.new_value, 
                    origin=OriginType.GOD_MODE
                )
            elif cmd.command_type == "INJECT_MONEY":
                # SettlementSystem을 통한 공식 자금 주입 (Magic Money 방지)
                self.settlement.inject_god_grant(cmd.target_agent_id, cmd.new_value)
            
            # 명령 처리 성공 로깅 (Watchtower 피드백용)
            self.logger.info(f"GodCommand Executed: {cmd.command_type}")
            
        except Exception as e:
            self.logger.error(f"GodCommand Failed: {str(e)}")
            # 에러 DTO 생성 후 Watchtower로 push 필요 (TBD)
```

---

## 4. Risk & Impact Audit (기술적 위험 분석)

- **명령 실행 순서**: 동일한 변수에 대한 여러 명령이 인입될 경우 큐의 순서(FIFO)를 엄격히 보장해야 합니다.
- **엔진 무결성**: `INJECT_MONEY`와 같은 명령이 `SettlementSystem`을 통하지 않고 에이전트의 `balance`를 직접 수정하면 Phase 8의 `total_m2_audit`이 즉시 실패합니다. 반드시 트랜잭션 로그를 남겨야 합니다.
- **Atomicity**: Phase 0에서 시작된 모든 변경사항은 Phase 1의 에이전트들이 "세상을 인지"하기 전에 완전히 반영되어야 합니다.

---

## 5. Testing & Verification Strategy

- **Test Intercept Timing**: Phase 0에서 `TAX_RATE`를 변경했을 때, 동일 틱의 Phase 2(Contract)에서 즉시 변경된 세율이 적용되는지 검증.
- **Test Rollback**: 유효하지 않은 `GodCommand` 주입 시 엔진이 크래시되지 않고 에러를 핸들링하는지 확인.

---

## 6. Mandatory Reporting Verification
Phase 0 도입에 따른 스케줄러 구조 변화 및 명령 큐 관리 전략에 대한 인사이트를 `communications/insights/FOUND-03-INTERCEPT.md`에 기록하였습니다.