# Technical Specification: UI-02 Dynamic Controls (The Cockpit Interface)

**Status**: Specification Draft  
**Mission Key**: UI-02  
**Target Module**: `dashboard/components/controls.py`  
**Orchestrator**: Antigravity (Architect Prime)  
**Scribe**: Gemini-CLI Administrative Assistant

---

## 1. Executive Summary
`GlobalRegistry`(FOUND-01)에 등록된 파라미터들을 관찰자가 실시간으로 제어할 수 있는 동적 UI 컴포넌트 라이브러리를 설계합니다. 본 모듈은 하드코딩된 UI 구성을 지양하고, 레지스트리의 메타데이터를 기반으로 슬라이더, 토글, 입력 필드를 자동 생성합니다. 특히 'God-Mode'의 권한 상태와 엔진의 'Sacred Sequence'를 UI 레벨에서 시각적으로 동기화하여 부정합한 조작을 원천 차단하는 데 목적이 있습니다.

---

## 2. Interface Specification (`dtos.py` 및 Schema 정의)

### 2.1 Registry Metadata Extension (The Missing Link)
`FOUND-01`의 `RegistryEntry`가 단순 값을 담는다면, `UI-02`는 이를 위젯으로 변환하기 위한 메타데이터 스키마를 정의합니다. 이 데이터는 `config/domains/schema.yaml`에서 로드되거나 Registry 초기화 시 주입됩니다.

```python
from typing import TypedDict, Any, List, Optional, Union
from enum import Enum

class WidgetType(Enum):
    SLIDER = "slider"
    TOGGLE = "toggle"
    NUMBER_INPUT = "number_input"
    SELECT = "select"

class ParameterSchemaDTO(TypedDict):
    """위젯 생성을 위한 메타데이터 정의"""
    key: str                # Registry Key (e.g., 'tax.corporate_rate')
    label: str              # UI 표시 명칭
    description: str        # 툴팁 설명
    widget_type: str        # WidgetType
    data_type: str          # 'int', 'float', 'bool'
    min_value: Optional[float]
    max_value: Optional[float]
    step: Optional[float]
    options: Optional[List[Any]] # Select 타입일 경우
    category: str           # UI 그룹핑 (e.g., 'Fiscal', 'Monetary')
```

### 2.2 GodCommandDTO (Command Routing)
사용자의 조작은 직접 Registry를 수정하지 않고 명령 객체로 캡슐화되어 전달됩니다.

```python
class GodCommandDTO(TypedDict):
    """관찰자 개입 명령 구조"""
    command_id: str
    key: str
    requested_value: Any
    origin: int            # OriginType.GOD_MODE
    timestamp: float
    require_ack: bool      # Phase 0 반영 확인 여부
```

---

## 3. Detailed Design (Logic & Pseudo-code)

### 3.1 Dynamic Discovery & Rendering
Dashboard 시작 시 `RegistrySchema`를 스캔하여 카테고리별로 UI 탭을 구성합니다.

```python
# dashboard/components/controls.py Pseudo-code

def render_dynamic_controls(registry_snapshot, schemas):
    for category in set(s['category'] for s in schemas):
        with st.expander(category):
            cat_schemas = [s for s in schemas if s['category'] == category]
            for schema in cat_schemas:
                entry = registry_snapshot.get(schema['key'])
                render_widget(schema, entry)

def render_widget(schema, entry):
    # 1. Lock State 확인
    is_disabled = entry.is_locked and entry.origin > OriginType.CONFIG
    
    # 2. 위젯 생성 (Streamlit 기준)
    col1, col2 = st.columns([0.9, 0.1])
    with col1:
        if schema['widget_type'] == "slider":
            new_val = st.slider(
                label=schema['label'],
                min_value=schema['min_value'],
                max_value=schema['max_value'],
                value=entry.value,
                disabled=is_disabled,
                key=f"ui_{schema['key']}"
            )
    with col2:
        # Lock Indicator 표시
        if entry.is_locked:
            st.markdown("🔒")
            
    # 3. 변경 감지 및 명령 전송 (Debounced)
    if new_val != entry.value:
        send_god_command(schema['key'], new_val)
```

### 3.2 Real-time Preview Buffer (Isolation Logic)
사용자가 슬라이더를 움직이는 동안 엔진 상태를 즉시 바꾸지 않고 UI 상에서만 'Preview' 상태를 유지합니다.

1.  **Input Phase**: 사용자가 슬라이더 조작.
2.  **Preview Phase**: UI는 즉시 'Pending' 상태 표시 (회색 처리 또는 스피너).
3.  **Command Phase**: `GodCommandDTO`가 백엔드로 전송됨.
4.  **Ack Phase**: 엔진의 `Phase 0`에서 명령이 수락되면, `Telemetry`를 통해 업데이트된 값이 UI로 돌아옴 -> 'Pending' 해제 및 값 확정.

---

## 4. 🕵️ Pre-flight Risk Analysis (Audit Response)

1.  **Metadata Deficiency**: `FOUND-01`의 단순 저장 구조를 보완하기 위해 `config/schema/` 경로에 별도의 YAML 기반 메타데이터 저장소를 구축하여 Registry와 1:1 매핑합니다.
2.  **Sacred Sequence Integrity**: 모든 UI 조작은 `GodCommandDTO` 큐를 거쳐 오직 `TickScheduler.phase_0_intercept()` 시점에서만 Registry에 반영되도록 설계하여 'Dirty Reads'를 방지합니다.
3.  **Command Jitter (Flicker)**: UI 컴포넌트에 `local_state`를 도입합니다. 서버로부터 ACK가 오기 전까지는 사용자가 마지막으로 조작한 값을 강제로 표시하고, 엔진 값과의 차이를 'Syncing...' 아이콘으로 노출합니다.
4.  **SRP Violation**: UI 로직(Streamlit 코드)은 오직 `dashboard/` 하위에만 위치하며, 엔진 모듈(`modules/`)은 오직 `GodCommandDTO`와 `RegistrySchema` 인터페이스만을 인지합니다.

---

## 5. Verification Plan (Testing)

### 5.1 핵심 테스트 케이스
- **Widget Discovery**: 특정 키의 스키마를 삭제했을 때 UI에서 해당 위젯이 크래시 없이 사라지는지 확인.
- **Lock Feedback**: `GlobalRegistry.lock(key)` 호출 시 UI 슬라이더가 즉시 비활성화(Disabled) 상태로 전환되는지 확인.
- **Atomic Rollback**: 유효 범위를 벗어난 값을 강제로 주입하는 명령 전송 시, 엔진에서 거부되고 UI가 이전 값으로 복구되는지 확인.
- **Latency Handling**: 네트워크 지연 모킹 환경에서 슬라이더 'Jitter'가 발생하지 않는지 검증.

### 5.2 Integration Check
- `UI-01` (Dashboard Shell)에서 `UI-02` 컴포넌트가 올바르게 임포트되어 렌더링되는지 확인.
- `DATA-01` (GodCommand) 명세와의 필드 일치 여부 검증.

---

## 6. Implementation Roadmap

1.  **Step 1**: `config/domains/registry_schema.yaml` 정의 및 로더 구현.
2.  **Step 2**: `dashboard/components/controls.py`에서 스키마 기반 동적 렌더링 로직 작성.
3.  **Step 3**: `GodCommandDTO` 발송을 위한 WebSocket 클라이언트 연동.
4.  **Step 4**: Lock 상태 및 Pending 상태 시각화 컴포넌트(CSS/Markdown) 추가.

---

## 7. Mandatory Reporting & Insights

**[Routine] Mandatory Reporting Instruction**: 
본 UI 설계 과정에서 발견된 'Streamlit의 상태 유지(Statefulness)와 엔진 틱 동기화 간의 임피던스 불일치' 및 '대규모 파라미터 렌더링 시의 프론트엔드 성능 저하'에 대한 분석 결과를 반드시 `communications/insights/UI_02_DYNAMIC_CONTROLS_INSIGHTS.md` 파일에 기록하십시오. 특히 위젯 ID 충돌 방지를 위한 네이밍 컨벤션 제안을 포함해야 합니다.

---
> **"조종석의 계기판은 비행기의 신경계와 연결되어야 한다. 사용자가 느끼는 피드백은 엔진의 물리적 진실과 일치해야만 한다."** - Administrative Scribe's Final Note