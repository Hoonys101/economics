# Specification: Watchtower Scaffolding (UI-01)

**Status**: Draft (Scribe)  
**Ref Version**: v1.1.0 (2026-02-13)  
**Mission Key**: GODMODE-WATCHTOWER-UI-SCAFFOLD  
**Lead Architect**: Antigravity  

---

## 1. 개요 (Executive Summary)

본 문서는 시뮬레이션의 전지적 관측 및 개입을 위한 `God-Mode Watchtower`의 프론트엔드 아키텍처와 스캐폴딩 설계를 정의합니다. Streamlit 프레임워크를 기반으로 하며, 시뮬레이션 엔진과의 통신은 `WebSocket`을 통해 비동기적으로 수행됩니다. 본 UI는 단순한 시각화를 넘어, 엔진의 `Phase 0 (Intercept)` 슬롯에 개입 명령을 주입하는 **'Command Cockpit'** 역할을 수행하며, 모든 상태 변경은 `GodCommandDTO` 계약을 준수합니다.

---

## 2. 인터페이스 및 데이터 계약 (Interface & Contract)

### 2.1 UI State Schema (Local Management)
Streamlit의 리런(Rerun) 특성을 고려하여 `st.session_state`를 통해 다음 상태를 관리합니다.

- **ConnectionState**: WebSocket 연결 객체, 지연 시간(Latency), 연결 유지 시간.
- **PendingCommands**: 아직 엔진으로 전송되지 않은 `GodCommandDTO`의 리스트 (Local Queue).
- **TelemetryBuffer**: 엔진으로부터 수신된 최신 `WatchtowerV2-DTO` 데이터 스냅샷.
- **RegistryMetadata**: `GlobalRegistry`로부터 가져온 파라미터 스키마 (최소/최대값, 타입, 설명).

### 2.2 Communication Bridge
- **SocketManager**: Streamlit 프로세스 내에서 WebSocket의 생명주기를 관리하는 싱글톤 서비스.
- **DTO Purity**: `dashboard/`는 `simulation/dtos/` 이하의 DTO 클래스만 참조하며, 엔진 내부 로직(`modules/*`)에 직접 접근하지 않습니다.

---

## 3. 레이아웃 설계 (Layout & Components)

대시보드는 **'Observe-Plan-Act'** 루프를 지원하도록 세 가지 주요 영역으로 구성됩니다.

### 3.1 Sidebar: Global Controls (The Registry)
- **Dynamic Slider Generator**: `RegistryMetadata`를 기반으로 파라미터를 동적으로 렌더링.
- **Domain Filter**: Economy, Government, Finance 등 도메인별 파라미터 그룹화.
- **Intervention Toggle**: 'Safe Mode'(관측 전용)와 'God Mode'(개입 가능) 전환 스위치.

### 3.2 Main: KPI Cockpit (The Telemetry)
- **Real-time Gauges**: 인플레이션, 실업률, GDP 성장률 등 핵심 지표 시각화.
- **Wealth Distribution Heatmap**: 에이전트 간 자산 분포를 실시간 히트맵으로 표시.
- **Tick Counter**: 현재 시뮬레이션 틱 및 TPS(Ticks Per Second) 표시.

### 3.3 Bottom: Command Center & Stream
- **Command Queue View**: 대기 중인 명령 목록 표시 및 개별 삭제 기능.
- **Bulk Commit Button**: 큐에 쌓인 명령을 `GodCommandDTO` 배열로 묶어 엔진으로 일괄 전송.
- **Audit Feed**: 엔진으로부터 반환된 `GodResponseDTO` 및 감사(Audit) 결과 로그 스트림.

---

## 4. 로직 단계 (Logic Steps & Pseudo-code)

### 4.1 UI-Side Command Lifecycle
1.  **Stage**: 사용자가 슬라이더 조절 시 `PendingCommands`에 DTO 생성 (엔진 통신 없음).
2.  **Verify**: UI 수준에서 데이터 타입 및 범위 1차 검증.
3.  **Commit**: 사용자가 버튼 클릭 시 `SocketManager`를 통해 WebSocket 전송.
4.  **Acknowledge**: 엔진으로부터 `GodResponseDTO` 수신 시 성공/실패 알림 표시 및 큐 비우기.

### 4.2 Pseudo-code: SocketManager Service

```python
# dashboard/services/socket_manager.py

class SocketManager:
    """Streamlit 리런 간에 WebSocket 연결을 유지하는 서비스 객체."""
    
    def __init__(self, uri: str):
        if 'ws_connection' not in st.session_state:
            self._connect(uri)
            
    def _connect(self, uri: str):
        # 비동기 루프를 사용하여 WebSocket 연결 수립
        # st.session_state.ws_connection 저장
        pass

    def send_command_batch(self, commands: List[GodCommandDTO]):
        payload = json.dumps([asdict(cmd) for cmd in commands])
        # WebSocket 전송 로직
        pass

    def get_latest_telemetry(self) -> Optional[WatchtowerV2DTO]:
        # 수신 버퍼에서 최신 데이터 추출
        pass
```

---

## 5. 예외 처리 및 복구 (Exception Handling)

| 예외 상황 | 대응 방안 | UI 피드백 |
| :--- | :--- | :--- |
| **Connection Lost** | `SocketManager`가 지수 백오프(Exponential Backoff)로 재연결 시도. | 상단 바에 'Disconnected' 경고 및 재시도 카운트다운 표시. |
| **Audit Rejected** | 엔진이 `GodResponseDTO(success=False)` 반환. | 명령 큐의 해당 항목을 빨간색으로 강조하고 `failure_reason` 툴팁 표시. |
| **Telemetry Lag** | 데이터 수신 주기가 임계값(e.g., 2초) 초과 시. | 시각화 컴포넌트 'Stale' 상태 표시 (회색 처리). |

---

## 6. 🚨 Risk & Impact Audit (기술적 위험 분석)

-   **GlobalRegistry Prerequisite (High)**: `FOUND-01` 미완료 시 UI의 동적 슬라이더 생성이 불가능하며, 하드코딩된 UI로 대체할 경우 엔진과의 상태 불일치 위험이 큼.
-   **Environment Leakage (High)**: Streamlit에서 `modules/` 내부의 객체를 직접 임포트할 경우, Python 인터프리터의 컨텍스트 충돌로 인해 시뮬레이션 엔진이 크래시될 수 있음. **오직 DTO만 임포트할 것을 강제함.**
-   **Blocking Process (Medium)**: WebSocket 수신 대기가 Streamlit의 메인 루프를 블로킹할 경우 UI가 얼어붙음. `asyncio` 또는 별도 스레드를 통한 비동기 수신 레이어 필수.
-   **State Desync**: 엔진이 롤백을 수행했을 때 UI 슬라이더 값이 이전 상태로 즉시 동기화되지 않으면 사용자 혼란 야기. `GodResponseDTO` 수신 시 슬라이더 값을 Registry의 현재 값으로 강제 업데이트하는 로직 필요.

---

## 7. 검증 계획 (Verification Strategy)

### 7.1 신규 테스트 케이스
-   `test_ui_command_queue_atomicity`: 여러 명령을 큐에 쌓고 일괄 전송 시, 모든 명령이 하나의 리스트로 직렬화되는지 검증.
-   `test_ui_dynamic_render_from_registry_mock`: Mock Registry Metadata를 주입했을 때 슬라이더가 올바른 범위와 레이블로 생성되는지 확인.

### 7.2 Integration Check
-   UI에서 'Commit' 버튼 클릭 후, 시뮬레이션 로그에서 `Phase 0 Intercept`가 해당 명령을 수신하여 처리하는지 확인.

---

## 8. Mandatory Reporting Verification

본 설계 과정에서 식별된 기술 부채와 인사이트를 다음 파일에 기록함.
-   **파일 위치**: `communications/insights/WATCHTOWER_UI_SCAFFOLD_INSIGHTS.md`
-   **기록 항목**:
    - Streamlit의 `st.empty()`를 활용한 실시간 차트 업데이트 성능 최적화 기법.
    - `GlobalRegistry`의 메타데이터 구조에 UI 힌트(e.g., `step_size`, `unit`) 추가 필요성.
    - 엔진-UI 간 시간 동기화(Tick vs Wall-clock)를 위한 텔레메트리 타임스탬프 규격 제안.

> **"조종석의 계기판은 엔진의 진실만을 말해야 하며, 모든 스위치는 원자적이어야 한다."** - Administrative Scribe's Final Note