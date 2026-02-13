# Specification: God-Mode Command Protocol (DATA-01)

**Status**: Draft (Scribe)  
**Ref Version**: v1.1.0 (2026-02-13)  
**Mission Key**: GODMODE-COMMAND-DTO  
**Lead Architect**: Antigravity  

---

## 1. 개요 (Executive Summary)

본 문서는 `God-Mode Watchtower`에서 전송된 개입 명령을 엔진이 안전하고 원자적으로(Atomic) 처리하기 위한 `GodCommandDTO` 규격과 **'Audit-Triggered Rollback'** 프로토콜을 정의합니다. 본 프로토콜은 시뮬레이션의 인과율을 보호하기 위해 `Sacred Sequence`의 **Phase 0 (Intercept)**에서만 실행되며, 금융 무결성 훼손 시 즉시 이전 상태로 복구하는 것을 원칙으로 합니다.

---

## 2. 인터페이스 명세 (Interface Specification)

### 2.1 `simulation/dtos/commands.py` (Draft)

모든 명령은 UUID 기반의 추적성을 가지며, 실행 결과와 롤백 여부를 포함하는 응답 DTO와 쌍을 이룹니다.

```python
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Literal
from uuid import UUID, uuid4

@dataclass(frozen=True)
class GodCommandDTO:
    """
    God-Mode 조작 명령을 위한 최상위 데이터 계약.
    """
    command_id: UUID = field(default_factory=uuid4)
    command_type: Literal["SET_PARAM", "TRIGGER_EVENT", "INJECT_ASSET", "PAUSE_STATE"] = "SET_PARAM"
    target_domain: str        # e.g., "Economy", "Government", "Finance"
    parameter_key: str        # e.g., "tax_rate", "harvest_multiplier"
    new_value: Any
    requester_id: str = "WATCHTOWER_UI"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class GodResponseDTO:
    """
    명령 실행 결과 및 감사(Audit) 리포트.
    """
    command_id: UUID
    success: bool
    execution_tick: int
    error_code: Optional[str] = None
    failure_reason: Optional[str] = None
    audit_report: Dict[str, Any] = field(default_factory=dict) # SettlementSystem 결과 포함
    rollback_performed: bool = False
```

---

## 3. 로직 단계 (Logic Steps & Pseudo-code)

### 3.1 `CommandService.execute_protocol()` (Execution Lifecycle)

명령은 반드시 다음 5단계의 수명 주기를 통과해야 합니다.

1.  **Validation (Phase 0.1)**:
    - `GlobalRegistry`에 해당 `target_domain`과 `parameter_key`가 존재하는지 확인.
    - 데이터 타입 및 도메인별 제약 조건(e.g., 세율 0~100%) 검증.
2.  **Snapshot (Phase 0.2)**:
    - 변경 전 `GlobalRegistry`의 현재 값을 `UndoStack`에 `(command_id, domain, key, old_value)` 형태로 저장.
3.  **Mutation (Phase 0.3)**:
    - `GlobalRegistry` 업데이트.
    - (이벤트인 경우) `EventQueue`에 즉시 실행 플래그와 함께 주입.
4.  **Integrity Audit (Phase 0.4)**:
    - `SettlementSystem.perform_integrity_check()` 호출.
    - 통화량(M2), 자산 합계 등 거시 경제 정합성 파손 여부 판정.
5.  **Commit or Rollback (Phase 0.5)**:
    - 감사 통과 시: 성공 응답 반환 및 로그 기록.
    - 감사 실패 또는 예외 발생 시: `UndoStack`을 사용하여 `GlobalRegistry`를 즉시 복구하고 `failure_reason`과 함께 실패 응답 반환.

### 3.2 Pseudo-code: Command Interceptor

```python
def process_god_commands(self, tick: int):
    commands = self.inbound_queue.consume_all()
    for cmd in commands:
        # 1. Snapshot
        old_val = GlobalRegistry.get(cmd.target_domain, cmd.parameter_key)
        self.undo_stack.push(cmd.command_id, cmd.target_domain, cmd.parameter_key, old_val)
        
        try:
            # 2. Execute
            GlobalRegistry.set(cmd.target_domain, cmd.parameter_key, cmd.new_value)
            
            # 3. Audit (Financial Integrity)
            audit_result = SettlementSystem.audit()
            if not audit_result.is_valid:
                raise IntegrityViolation(audit_result.reason)
                
            self.broadcast_response(GodResponseDTO(cmd.command_id, True, tick))
            
        except Exception as e:
            # 4. Atomic Rollback
            recovery_data = self.undo_stack.pop(cmd.command_id)
            GlobalRegistry.set(recovery_data.domain, recovery_data.key, recovery_data.old_value)
            
            self.broadcast_response(GodResponseDTO(
                command_id=cmd.command_id,
                success=False,
                execution_tick=tick,
                failure_reason=str(e),
                rollback_performed=True
            ))
```

---

## 4. 예외 처리 (Exception Handling)

| 예외 상황 | 대응 방안 | 응답 코드 |
| :--- | :--- | :--- |
| **Registry Key Not Found** | 실행 전 차단, 상태 변경 없음. | `ERR_INVALID_TARGET` |
| **Type Mismatch** | `new_value` 타입 불일치 시 차단. | `ERR_TYPE_MISMATCH` |
| **Integrity Violation** | 실행 후 롤백 수행 (SettlementSystem 감지). | `ERR_AUDIT_FAILURE` |
| **Government God-Class Conflict** | 분리 전 정부 변수 수정 시 경고 로그 및 제한적 허용. | `WARN_DEPRECATED_ACCESS` |

---

## 5. 🚨 Risk & Impact Audit (기술적 위험 분석)

-   **GlobalRegistry Prerequisite (High)**: `FOUND-01` 미완료 시 본 설계는 작동 불가능함. 하드코딩된 상수를 직접 수정하는 방식은 절대 금지함.
-   **Government Decomposition (Medium)**: `Government` 모듈이 현재 God-Class 상태이므로, 세금/복지 파라미터 수정 시 `Government` 내부의 캐싱된 상태(Stale Data)와 `Registry` 간의 불일치가 발생할 수 있음. 선행 작업으로 `Government.sync_with_registry()` 메서드 구현 필요.
-   **Rollback Scope**: 본 설계의 롤백은 `GlobalRegistry`에 한정됨. 만약 명령이 에이전트의 내부 변수(e.g., `agent.wealth`)를 직접 수정했다면 복구가 불가능함. 따라서 **God-Mode는 오직 Registry와 EventQueue를 통해서만 개입해야 함**을 강제함.

---

## 6. 검증 계획 (Verification Strategy)

### 6.1 신규 테스트 케이스
-   `test_atomic_rollback_on_audit_failure`: 고의로 M2 정합성을 깨뜨리는 `INJECT_MONEY` 명령을 주입하고, `GlobalRegistry`가 이전 값으로 복구되는지 검증.
-   `test_phase_0_enforcement`: Phase 0 이외의 시점에서 명령 실행 시도 시 거부되는지 확인.

### 6.2 Integration Check
-   명령 실행 후 `WatchtowerV2-DTO`의 텔레메트리 데이터가 변경된 파라미터를 정확히 반영하는지 확인 (UI 동기화 검증).

---

## 7. Mocking 가이드

-   **Golden Samples**: `tests/fixtures/god_commands/`에 표준 `SET_PARAM` 샘플 JSON을 비치하여 테스트 시 로드.
-   **Audit Mocking**: `SettlementSystem.audit()`을 모킹하여 강제로 실패를 유도하는 시나리오 테스트 필수.

---

## 8. Mandatory Reporting Verification

본 설계 과정에서 식별된 기술 부채와 인사이트를 다음 파일에 기록함.
-   **파일 위치**: `communications/insights/GODMODE_PROTOCOL_DATA_01.md`
-   **기록 항목**:
    - `GlobalRegistry` 도입 시 기존 `economy_params.yaml` 로드 시점의 정합성 문제.
    - `UndoStack`의 메모리 비대화 방지를 위한 최대 스택 크기 및 자동 소멸 정책 제안.
    - `IntegrityViolation` 발생 시 UI에 노출할 사용자 친화적 에러 메시지 매핑 전략.

> **"명령은 강력해야 하지만, 그 책임(Rollback)은 완벽해야 한다."** - Administrative Scribe's Final Note