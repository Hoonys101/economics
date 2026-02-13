# Specification: Production Integration - Watchtower & Engine (INT-01)

**Status**: Draft (Scribe)  
**Ref Version**: v1.1.0 (2026-02-13)  
**Mission Key**: GODMODE-WATCHTOWER-INTEGRATION  
**Lead Architect**: Antigravity  

---

## 1. 개요 (Executive Summary)

본 문서는 `God-Mode Watchtower` UI와 실제 시뮬레이션 엔진 간의 실시간 통합(Production Wiring) 설계를 정의합니다. 핵심 목표는 엔진의 계산 루프(Tick Loop)와 WebSocket 서버의 통신 루프를 스레드 안전하게 결합하여, **Phase 0 (Intercept)**에서 명령을 주입하고 **Phase 8 (Broadcast)**에서 텔레메트리를 추출하는 것입니다. 본 설계는 엔진의 무결성을 최우선으로 하며, 네트워크 지연이 엔진의 TPS(Ticks Per Second)에 영향을 주지 않는 'Non-blocking Observer' 패턴을 지향합니다.

---

## 2. 인터페이스 및 데이터 계약 (Interface & Contract)

### 2.1 Communication DTOs
- **GodCommandDTO**: `simulation/dtos/commands.py`에 정의된 명령 객체. 엔진의 `GlobalRegistry` 파라미터 수정을 위한 `key`, `value` 및 메타데이터 포함.
- **WatchtowerV2DTO**: `simulation/dtos/telemetry.py`에 정의된 엔진 상태 스냅샷. 거시 경제 지표 및 에이전트 통계 요약 포함.

### 2.2 Thread-Safe Primitives (The Bridge)
- **CommandQueue**: `queue.Queue[GodCommandDTO]` (Max size: 100). 서버가 저장하고 엔진이 소비.
- **TelemetryExchange**: `AtomicReference` 또는 `multiprocessing.Manager.Value` 스타일의 단일 슬롯 버퍼. 엔진이 최신 스냅샷을 덮어쓰고 서버가 읽어감.

---

## 3. 시스템 아키텍처 (Concurrency Model)

엔진과 서버는 독립적인 스레드에서 실행되며, 오직 정의된 Bridge 객체를 통해서만 데이터를 교환합니다.

### 3.1 Simulation Thread (The Producer/Consumer)
- **TickScheduler**가 루프를 주도.
- **Phase 0 (Intercept)**: `CommandQueue`를 확인하여 대기 중인 명령을 `GlobalRegistry`에 반영.
- **Phase 8 (Broadcast)**: 현재 상태의 Read-only 스냅샷을 생성하여 `TelemetryExchange`에 저장.

### 3.2 Server Thread (The Adapter)
- `SimulationServer` (WebSocket 기반)가 클라이언트(Streamlit) 연결 관리.
- **Input**: 클라이언트로부터 수신된 JSON을 `GodCommandDTO`로 역직렬화하여 `CommandQueue`에 삽입.
- **Output**: 주기적으로 (e.g., 100ms) `TelemetryExchange`에서 최신 데이터를 읽어 연결된 모든 클라이언트에 브로드캐스트.

---

## 4. 로직 단계 (Logic Steps & Pseudo-code)

### 4.1 Phase 0: Command Injection (Engine Side)
```python
def phase_0_intercept(self):
    """엔진 틱 시작 시 명령 소비."""
    while not self.command_queue.empty():
        cmd = self.command_queue.get_nowait()
        try:
            # GlobalRegistry를 통한 원자적 반영
            success = self.registry.apply_command(cmd)
            self.audit_log.append(GodResponseDTO(cmd.id, success=success))
        except Exception as e:
            self.audit_log.append(GodResponseDTO(cmd.id, success=False, error=str(e)))
```

### 4.2 Phase 8: Telemetry Harvesting (Engine Side)
```python
def phase_8_broadcast(self):
    """엔진 틱 종료 시 스냅샷 생성."""
    # Read-only 뷰 생성 (Deepcopy 지양, DTO 변환 선호)
    snapshot = self.telemetry_collector.capture_snapshot()
    self.telemetry_exchange.update(snapshot)
```

### 4.3 Production Wiring (Initialization)
```python
# main.py 또는 SimulationInitializer

def start_integrated_simulation():
    command_queue = queue.Queue()
    telemetry_exchange = TelemetryBuffer()
    
    # 1. 서버 시작 (Background Thread)
    server = SimulationServer(host="0.0.0.0", port=8765, 
                              cmd_q=command_queue, 
                              tele_ex=telemetry_exchange)
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    
    # 2. 엔진 생성 및 훅 등록
    engine = SimulationEngine(config=cfg)
    engine.scheduler.register_hook(Phase.ZERO, lambda: phase_0_intercept(command_queue))
    engine.scheduler.register_hook(Phase.EIGHT, lambda: phase_8_broadcast(telemetry_exchange))
    
    # 3. 엔진 실행 (Main Thread)
    engine.run()
```

---

## 5. 예외 처리 및 복구 (Exception Handling)

| 상황 | 대응 방안 |
| :--- | :--- |
| **Command Validation Failure** | `GlobalRegistry` 수준에서 범위(Range) 체크 실패 시 명령을 버리고 `AuditLog`에 실패 기록. |
| **Server Thread Crash** | 엔진은 서버 상태와 무관하게 틱을 지속. `main.py`에서 서버 스레드 생존 여부 감시 및 재시작 시도. |
| **Telemetry Buffer Overflow** | 서버가 데이터를 처리하는 속도보다 엔진 틱이 빠를 경우, 가장 오래된 텔레메트리는 덮어씌워짐 (LIFO 스타일). |

---

## 6. 🚨 Risk & Impact Audit (기술적 위험 분석)

- **Government God Class Side-effects (High)**: `GlobalRegistry`를 통해 세금이나 복지 파라미터를 수정할 때, `modules/government` 내부의 복잡한 연쇄 반응이 발생할 수 있음. **FOUND-02 (Service Separation)** 완료 전에는 개입 범위를 제한할 것을 권고함.
- **Thread-Safety & Race Conditions (High)**: `Phase 8`에서 텔레메트리를 수집하는 동안 엔진의 다른 부분에서 상태를 수정하면 안 됨. 수집 로직은 반드시 `SettlementSystem`이 완료된 정적인 상태에서 수행되어야 함.
- **Circular Import Risk (Medium)**: `SimulationServer`가 엔진 내부 모듈을 참조하지 않도록 해야 함. 서버는 오직 `CommandQueue`와 `TelemetryExchange`라는 추상적인 통로만 알아야 함 (Dependency Inversion).
- **Network Blocking (Low)**: WebSocket 브로드캐스트 로직에 `await`이나 blocking I/O가 포함되어 엔진 스레드를 멈추지 않도록 서버 스레드에서만 소켓 작업을 수행함.
- **Missing Library (Critical)**: 현재 CI 환경에 `websockets` 라이브러리가 없음. `requirements.txt` 업데이트와 함께 테스트 환경에서 Mocking 전략 필수.

---

## 7. 검증 계획 (Verification Strategy)

### 7.1 신규 테스트 케이스
- `test_engine_command_consumption_atomicity`: `CommandQueue`에 10개의 명령을 넣고 한 틱(Phase 0) 내에 모두 처리되는지 확인.
- `test_telemetry_snapshot_integrity`: 엔진 상태 변화 직후 `Phase 8`에서 생성된 DTO가 원본 데이터와 일치하는지 검증.
- `test_server_engine_concurrency`: 서버 스레드에서 초당 100회 명령 주입 시 엔진 TPS 저하가 5% 이내인지 측정.

### 7.2 Integration Check
- `scripts/forensics_launcher.py`를 사용하여 엔진과 Watchtower UI를 동시 실행하고, UI 슬라이더 조작 시 엔진 로그에 `Registry updated` 메시지가 출력되는지 확인.

---

## 8. Mandatory Reporting Verification

본 설계 및 분석 과정에서 발견된 기술 부채와 인사이트를 다음 파일에 기록함.
- **파일 위치**: `communications/insights/GODMODE_INTEGRATION_INSIGHTS.md`
- **기록 항목**:
    - `GlobalRegistry` 도입 시 기존 `economy_params.yaml` 로딩 로직과의 정합성 유지 방안.
    - `Government` 모듈 내 `TaxSystem`의 상태 의존성 제거를 위한 `Stateless Engine` 전환 가이드.
    - `websockets` 라이브러리 부재에 따른 CI 통과용 Mock Server 작성 가이드.

---

## 9. API 초안 (`modules/system/server_api.py`)

```python
from typing import Protocol, List
from simulation.dtos.commands import GodCommandDTO
from simulation.dtos.telemetry import WatchtowerV2DTO

class SimulationServerInterface(Protocol):
    """외부 시각화 도구와의 통신을 담당하는 서버 인터페이스."""
    
    def start(self, host: str, port: int) -> None:
        """서버를 비동기 스레드에서 시작함."""
        ...

    def stop(self) -> None:
        """서버를 안전하게 종료함."""
        ...

    def broadcast_telemetry(self, data: WatchtowerV2DTO) -> None:
        """연결된 모든 클라이언트에 상태 데이터를 전송함."""
        ...

    def get_pending_commands(self) -> List[GodCommandDTO]:
        """클라이언트로부터 수신되어 대기 중인 명령 목록을 반환함."""
        ...
```

> **"연결은 부드러워야 하고, 엔진은 단단해야 한다. 네트워크의 노이즈가 시뮬레이션의 진실을 방해하게 두지 마라."** - Administrative Scribe's Final Note