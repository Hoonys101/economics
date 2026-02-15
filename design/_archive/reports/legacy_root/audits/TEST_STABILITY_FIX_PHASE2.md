# 테스트 결함 진단 및 복구 사양서 (Fix Spec)

**작성자**: Senior SDET / Architect
**대상**: 15개 주요 테스트 실패 사례 (Post-Merge)
**상태**: 분석 완료 및 솔루션 확정

---

## 1. 결함 진단 보고 (Executive Summary)

현재 발생한 15개의 실패 사례는 크게 **세 가지 아키텍처적 충돌**에서 기인합니다.
1.  **의존성 주입(DI) 계약 위반**: `Simulation` 엔진 초기화 시 `registry`, `settlement_system`, `agent_registry`가 필수로 요구되도록 변경되었으나, 기존 테스트 코드들이 이를 반영하지 못해 `TypeError` 발생.
2.  **서비스 인터페이스 파손 (Breaking Change)**: `CommandService`에서 `pop_commands()` 메서드가 제거되고 `execute_command_batch` 체제로 전환되었으나, `Simulation` 엔진(L96)과 레거시 테스트들이 여전히 구형 API를 호출 중.
3.  **런타임 환경 설정 불일치**: `pytest-asyncio`가 설정 파일(`pytest.ini`)에는 존재하나 실제 테스트 실행 환경에서 `async def`를 처리하지 못하는 마킹 오류 발생.

---

## 2. 상세 기술 분석 및 해결책

### 2.1. Simulation & CommandService 초기화 오류
-   **현상**: `TypeError: CommandService.__init__() missing 3 required positional arguments...`
-   **원인**: `simulation/engine.py`의 `__init__`에서 `CommandService`를 생성할 때 인자를 전달하지만, 테스트 코드에서 `Simulation` 객체를 생성할 때 필요한 Mock 객체들을 주입하지 않음.
-   **해결책**: 모든 통합/시스템 테스트의 `setup` 단계에서 `MagicMock(spec=IGlobalRegistry)`, `MagicMock(spec=ISettlementSystem)`, `MagicMock(spec=IAgentRegistry)`를 생성하여 `Simulation`에 주입하도록 수정.

### 2.2. CommandService API 불일치 (`pop_commands`)
-   **현상**: `simulation/engine.py:L96`에서 `self.command_service.pop_commands()` 호출 시 오류 (해당 메서드 존재하지 않음).
-   **원인**: 신규 `CommandService`는 원자적 배치 실행(`execute_command_batch`)에 집중하도록 설계되어 기존의 단순 큐 방식(`pop`)이 제거됨.
-   **해결책**: 
    -   `CommandService`에 내부 제어용 큐(Internal Control Queue)를 복구하거나, `Simulation._process_commands`를 `execute_command_batch`를 호출하는 방식으로 리팩토링.
    -   테스트에서 사용되는 `GodCommandDTO` 생성 시 `target_agent_id`가 키워드 인자로 허용되지 않는 문제(`test_intercept.py:35`)는 DTO 정의에 필드를 추가하거나 `payload` 딕셔너리로 이동.

### 2.3. Asyncio 테스트 실행 오류
-   **현상**: `Failed: async def functions are not natively supported.` 및 `PytestUnknownMarkWarning`.
-   **원인**: `pytest-asyncio` 플러그인이 로드되지 않았거나, `pytest.ini`와 실제 환경 간의 버전 충돌.
-   **해결책**: `requirements.txt` 내 `pytest-asyncio` 버전 확인 및 `pytest.ini`에 `asyncio_default_fixture_loop_scope = function` (버전에 따라 필요시) 추가.

### 2.4. 재정 정책 및 원자성 논리 오류
-   **현상**: `test_debt_ceiling_enforcement` (0 == 500.0) 실패.
-   **원인**: `CommandService`의 `rollback_last_tick` 과정에서 재정 한도 도달 시 값이 0으로 초기화되거나, `registry.set`의 결과가 즉시 반영되지 않는 격리 문제.
-   **해결책**: `GlobalRegistry`의 `origin` 권한(OriginType.GOD_MODE)이 올바르게 전달되는지 확인하고, `audit_total_m2` 실패 시 롤백 로직이 재정 매개변수까지 완벽히 복구하는지 검증.

---

## 3. Jules를 위한 작업 분할 구조 (WBS)

| ID | 모듈 | 작업 내용 | 우선순위 |
| :--- | :--- | :--- | :--- |
| **WBS-1** | `Core Engine` | `simulation/engine.py` 내 `_process_commands`를 신규 `CommandService` API에 맞게 리팩토링 | High |
| **WBS-2** | `Services` | `modules/system/services/command_service.py`에 레거시 호환을 위한 `pop_commands` (Internal 전용) 추가 또는 API 브릿지 구현 | High |
| **WBS-3** | `DTO` | `simulation/dtos/commands.py` 내 `GodCommandDTO`에 `target_agent_id` 필드 공식 추가 (Property 또는 Field) | Medium |
| **WBS-4** | `Test Infrastructure` | `tests/conftest.py` 또는 각 테스트 클래스의 `setup` 메소드에 신규 DI 요구사항(3개 Registry/System) Mock 주입 로직 일괄 적용 | High |
| **WBS-5** | `Integration Fix` | `tests/integration/test_server_integration.py`의 `pytest.mark.asyncio` 경고 해결 및 비동기 루프 정상화 | Medium |
| **WBS-6** | `Logic Audit` | `test_fiscal_policy.py`의 부채 한도 테스트 실패 원인 분석 및 `CommandService.rollback` 정합성 수정 | Medium |

---

## 4. 최종 진단 결과 (Test Doctor Summary)

1. **Failing Module**: `tests/system/test_engine.py`, `tests/integration/test_cockpit_integration.py` 등 다수
2. **Error**: `TypeError: __init__() missing 3 positional arguments` & `AttributeError: no attribute 'pop_commands'`
3. **Diagnosis**: `Simulation`과 `CommandService` 간의 DI 계약 및 API 명세가 머지 과정에서 불일치함. 모든 테스트 초기화 코드에 `registry`, `settlement_system`, `agent_registry` Mock 주입이 필요하며, 엔진의 명령 처리 로직을 신규 배치 실행 모델로 전환해야 함.