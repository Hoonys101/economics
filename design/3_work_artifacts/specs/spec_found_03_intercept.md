# Specification Draft: Phase 0 (Intercept) - The Sovereign Slot

**Status**: Draft (Scribe)  
**Ref Version**: v1.0.0 (2026-02-13)  
**Mission Key**: FOUND-03  
**Orchestrator**: Antigravity (Architect Prime)

---

## 1. 개요 (Executive Summary)

`Phase 0 (Intercept)`는 'Sacred Sequence'의 최상단에 위치하여 시뮬레이션의 인과율이 시작되기 전, 외부(Watchtower)로부터 인입된 개입 명령을 집행하는 소버린 슬롯(Sovereign Slot)입니다. 본 명세는 `TickScheduler`가 외부 명령을 안전하게 소비하고, `GlobalRegistry` 및 `SettlementSystem`과 협력하여 무결성을 유지하며 상태를 변경하는 메커니즘을 정의합니다.

### 1.1 핵심 목표
- **Causality Protection**: 시뮬레이션 틱의 내부 로직(Phase 1~8)이 시작되기 전 모든 거시/미시 변수 수정을 완료.
- **Atomic Integrity**: 명령 집행 직후 `Total M2 Audit`을 강제 수행하여 '신비한 자금(Magic Money)' 생성을 원천 차단.
- **Decoupling**: 스케줄러는 집행의 '시기'만 결정하고, 실제 로직은 `CommandService`에 위임하여 SRP(단일 책임 원칙) 준수.

---

## 2. 인터페이스 명세 (Interface Specification)

### 2.1 Command Service Interface (modules/system/services/command_service.py)
스케줄러와 도메인 로직 간의 결합도를 낮추기 위한 중계 인터페이스입니다.

```python
from typing import List
from simulation.dtos.commands import GodCommandDTO

class ICommandService:
    """God-Mode 명령의 유효성 검증 및 집행을 담당하는 서비스 인터페이스."""
    
    def dispatch_commands(self, commands: List[GodCommandDTO]) -> List[str]:
        """
        명령 목록을 순차적으로 집행하고 처리 결과를 반환합니다.
        
        Args:
            commands: Watchtower로부터 인입된 명령 DTO 목록.
            
        Returns:
            List[str]: 각 명령의 처리 결과 메시지 (성공/실패 사유).
        """
        ...

    def rollback_last_tick(self) -> bool:
        """UndoStack을 사용하여 이전 틱의 개입 상태로 복구합니다."""
        ...
```

### 2.2 GlobalRegistry Abstraction (FOUND-01 연계)
`Phase 0` 구현 시 참조할 레지스트리 접근 방식입니다.

```python
class GlobalRegistry:
    @staticmethod
    def set_param(domain: str, key: str, value: Any, owner: str = "GodMode") -> None:
        """
        런타임 파라미터를 업데이트합니다. 
        'GodMode' owner로 설정 시 엔진 내 자동 조정 로직에 의해 덮어씌워지지 않도록 락을 겁니다.
        """
        ...
```

---

## 3. 로직 단계 (Pseudo-code)

### 3.1 TickScheduler Integration (modules/system/scheduler.py)
기존 `run_tick` 루프에 `Phase 0`를 삽입하는 구조입니다.

```python
# TickScheduler 내부 로직
def run_tick(self):
    """Sacred Sequence: Phase 0 to 8"""
    
    # [Phase 0: Intercept] -----------------------------------------
    # 1. 커맨드 버퍼로부터 대기 중인 God-Mode 명령 인출
    pending_commands = self.inbox.get_all_commands()
    
    if pending_commands:
        # 2. CommandService에 집행 위임 (SRP 준수)
        # 스케줄러는 CommandService를 DI(Dependency Injection)로 주입받음
        results = self.command_service.dispatch_commands(pending_commands)
        
        # 3. 무결성 강제 검증 (Audit Gate)
        # 개입 직후 M2 합계가 깨졌다면 즉시 Panic 및 Rollback
        if not self.settlement_system.audit_total_m2():
            self.logger.critical("God-Mode intervention corrupted M2 integrity!")
            self.command_service.rollback_last_tick()
            raise IntegrityError("M2 Audit Failed after God-Mode Intercept")
    
    # [Phase 1: Perception] ----------------------------------------
    self.execute_phase_1_perception()
    
    # ... Phase 2 ~ 7 집행 ...
    
    # [Phase 8: Telemetry & Harvest] -------------------------------
    self.execute_phase_8_telemetry()
```

### 3.2 CommandService Dispatch Logic
명령의 실제 처리 흐름입니다.

```python
def dispatch_commands(self, commands):
    for cmd in commands:
        # 1. Snapshot for Undo
        # 명령 적용 전 해당 도메인의 현재 상태를 UndoStack에 저장
        self.undo_stack.push(cmd.target_domain, GlobalRegistry.get_param(cmd.target_domain, cmd.parameter_name))
        
        # 2. Validation
        # 도메인별 제약 조건 확인 (e.g., 세율은 0~1 사이여야 함)
        if not self.validator.is_valid(cmd):
            continue
            
        # 3. Execution
        if cmd.command_type == "SET_PARAM":
            GlobalRegistry.set(cmd.target_domain, cmd.parameter_name, cmd.new_value, origin=OriginType.GOD_MODE)
        elif cmd.command_type == "INJECT_MONEY":
            # 돈을 주입할 경우 반드시 SettlementSystem의 특별 트랜잭션 사용
            self.settlement_system.mint_and_distribute(cmd.target_agent_id, cmd.amount)
```

---

## 4. 예외 처리 및 롤백 (Exception Handling)

- **Audit Failure**: `Phase 0` 명령 집행 후 `settlement_system.audit_total_m2()`가 `False`를 반환하면, 시뮬레이션을 `PAUSED` 상태로 전환하고 `UndoStack`을 팝하여 명령 이전 상태로 강제 복구합니다.
- **Invalid Parameter Range**: 유효 범위를 벗어난 값(예: `TAX_RATE = 1.5`)이 인입될 경우, 해당 명령만 스킵하고 에러 로그를 Watchtower DTO에 실어 보냅니다. 엔진은 크래시되지 않아야 합니다.

---

## 5. 검증 계획 (Testing & Verification Strategy)

### 5.1 신규 테스트 케이스 (Happy Path & Edge Case)
1. **test_intercept_causality**: `Phase 0`에서 수정된 `CHILD_MONTHLY_COST`가 동일 틱의 `Phase 1 (Perception)`에서 에이전트의 예산 제약에 즉시 반영되는지 확인.
2. **test_minting_integrity_audit**: `INJECT_MONEY` 명령으로 M2 통화량이 변했을 때, `SettlementSystem`이 이를 '정당한 발행'으로 인지하고 Audit을 통과시키는지, 아니면 'Magic Money'로 판정하여 차단하는지 검증.
3. **test_command_isolation**: 여러 개의 `SET_PARAM` 명령이 순차적으로 들어왔을 때, 앞선 명령의 실패가 뒤쪽 명령의 실행에 영향을 주지 않는지 확인.

### 5.2 Existing Test Impact
- **Sacred Sequence Hook Tests**: `Phase` 번호를 하드코딩하여 Hook을 거는 테스트들은 인덱스 조정이 필요함. (Phase 0 추가로 인해 기존 1~8이 밀리지 않도록 Enum 기반 접근 권장)

---

## 6. 🚨 Risk & Impact Audit (기술적 위험 분석)

- **순환 참조 위험 (Circular Dependency)**: `TickScheduler`가 `CommandService`를 참조하고, `CommandService`가 다시 `TickScheduler`의 틱 카운트를 참조하는 구조를 피해야 합니다. `CommandService`는 오직 `Registry`와 `SettlementSystem`에만 의존하도록 설계하십시오.
- **Performance Overhead**: 매 틱마다 `inbox.get_all_commands()`를 수행하는 비용은 무시할 수 있으나, 명령이 존재할 때 수행하는 `Audit` 비용은 시뮬레이션 속도를 저하시킬 수 있습니다. 명령이 있을 때만 조건부 Audit을 수행합니다.
- **Government Module Decoupling**: TD-226~229가 미완료된 상태에서 `Government` 내부 변수를 `Phase 0`에서 직접 수정할 경우, 정부 모듈의 캐싱된 상태와 불일치가 발생할 수 있습니다. `GlobalRegistry`를 통한 'Single Source of Truth' 접근이 필수적입니다.

---

## 7. Mandatory Reporting Verification

- **인사이트 보고**: 본 명세 설계 과정에서 식별된 `TickScheduler`의 Phase 관리 방식(List vs Enum)에 대한 부채와 `SettlementSystem`의 Audit 예외 처리 로직에 대한 인사이트를 `communications/insights/FOUND_03_INTERCEPT_DESIGN.md`에 기록함. 
- **보고서 작성 지시**: 구현 담당 Jules는 작업 완료 후 위 경로에 리포트를 남기지 않을 시 미션 실패로 간주됨을 인지하십시오.

---
> **"Phase 0은 신의 개입이 인과율의 질서로 편입되는 유일한 통로이다. 이곳의 무결성이 곧 세계의 실존이다."** - Administrative Scribe's Final Note