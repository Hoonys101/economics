# [Report] System-Wide Command & Integration Integrity Audit

## Executive Summary
최근의 테스트 실행 결과, 시뮬레이션 엔진과 `CommandService` 간의 **의존성 주입(Dependency Injection) 불일치**로 인해 대규모 `TypeError`가 발생하고 있습니다. 또한, `GodCommandDTO` 명세 변경에 따른 테스트 코드의 파편화와 `asyncio` 테스트 환경 설정 누락이 주요 병목 지점으로 확인되었습니다. 총 15개 실패 항목 중 80% 이상이 `CommandService` 초기화 오류에 기인합니다.

---

## Root Cause Analysis (RCA)

### 1. `CommandService` 초기화 시그니처 불일치
- **현상**: `TypeError: CommandService.__init__() missing 3 required positional arguments`
- **원인**: `simulation/engine.py:L50`에서 `CommandService()`를 인자 없이 호출하고 있으나, `modules/system/services/command_service.py:L100` 정의부에서는 `registry`, `settlement_system`, `agent_registry` 3개의 필수 인자를 요구합니다.
- **영향**: 시뮬레이션 엔진 초기화 자체가 실패하여 대부분의 통합/시스템 테스트가 중단됨.

### 2. `GodCommandDTO` 필드 스키마 충돌
- **현상**: `TypeError: GodCommandDTO.__init__() got an unexpected keyword argument 'target_agent_id'`
- **원인**: `simulation/dtos/commands.py:L8`의 DTO는 `target_agent_id`를 생성자 인자로 허용하지 않는 `frozen=True` 데이터클래스입니다. 반면, `test_intercept.py` 등의 기존 테스트 코드는 해당 필드를 직접 전달하고 있습니다.
- **영향**: God-Mode 명령 인터셉트 및 실행 검증 실패.

### 3. Asyncio 테스트 환경 미설정
- **현상**: `Failed: async def functions are not natively supported.` 및 `PytestUnknownMarkWarning`
- **원인**: `pytest-asyncio` 플러그인이 활성화되지 않았거나, `pytest.ini`에 `asyncio_mode` 설정이 누락되었습니다.
- **영향**: 서버 브리지 및 텔레메트리 관련 비동기 통합 테스트 실행 불가.

---

## Work Breakdown Structure (WBS)

### Group A: Simulation Engine Core (Fix Priority: High)
- **목표**: `CommandService` 의존성 전파 및 초기화 로직 정상화.
- **담당 파일**: `simulation/engine.py`, `simulation/initialization/initializer.py`

### Group B: Protocol & DTO Alignment (Fix Priority: Medium)
- **목표**: `GodCommandDTO` 스키마와 테스트 코드 간의 계약(Contract) 일치.
- **담당 파일**: `simulation/dtos/commands.py`, `tests/unit/simulation/orchestration/phases/test_intercept.py`

### Group C: Infrastructure & Test Environment (Fix Priority: Medium)
- **목표**: 비동기 테스트 지원 및 `pytest` 경고 제거.
- **담당 파일**: `pytest.ini`, `requirements.txt` (검토)

---

## Fix Specification

### 1. `CommandService` Wiring 수정
- **파일**: `simulation/engine.py`
- **수정**: `__init__`에서 필요한 서비스를 인자로 전달받도록 수정.
  ```python
  # 기존
  self.command_service = CommandService()
  # 수정 제안
  def __init__(self, ..., registry, settlement_system, agent_registry):
      ...
      self.command_service = CommandService(registry, settlement_system, agent_registry)
  ```
- **파일**: `simulation/initialization/initializer.py`
- **수정**: `build_simulation` 메소드 내에서 생성된 `GlobalRegistry`, `SettlementSystem`, `AgentRegistry`를 `Simulation` 인스턴스에 올바르게 주입.

### 2. `GodCommandDTO` 확장
- **파일**: `simulation/dtos/commands.py`
- **수정**: `@property`로만 존재하는 `target_agent_id`와 `amount`를 선택적 필드로 승격하거나, `metadata`를 통한 매핑 로직 강화. (테스트 호환성을 위해 필드 추가 권장)

### 3. Pytest Asyncio 설정
- **파일**: `pytest.ini`
- **수정**: 아래 내용 추가 확인.
  ```ini
  [pytest]
  asyncio_mode = auto
  markers =
      asyncio: mark test as an asyncio test
  ```

### 4. Fiscal Policy Logic 검증 (`test_debt_ceiling_enforcement`)
- **파일**: `modules/finance` 또는 `modules/government` 내 부채 한도 제어 로직.
- **분석**: `assert 0 == 500.0` 오류는 부채 한도 도달 시 정책이 0을 반환하거나 한도 자체가 적용되지 않음을 시사. `SettlementSystem`의 `audit` 연동 여부 확인 필요.

## Risk Assessment
- **Breaking Changes**: `CommandService` 생성자 변경은 이를 수동으로 Mocking하는 모든 단위 테스트 파일의 수정을 동반해야 합니다.
- **Side Effects**: `SimulationInitializer`에서의 주입 순서가 꼬일 경우 `AttributeError`가 발생할 수 있으므로, `GlobalRegistry` 생성 직후 주입이 이루어져야 합니다.

## Conclusion
현재 발생한 오류의 대다수는 **시스템 구성 요소 간의 Interface Mismatch**입니다. `SimulationInitializer`를 중심으로 한 의존성 주입 구조를 재정비하고, `GodCommandDTO`의 필드 정의를 최신화하면 대부분의 실패 케이스가 해결될 것으로 보입니다. 즉시 `Fix Specification`에 따른 코드 수정 작업(Jules Mission) 착수를 권고합니다.