# 🐙 Code Review Report: Mission UI-03 (Scenario Visualizers & On-Demand Telemetry)

**Reviewer**: Gemini-CLI Subordinate (Lead Code Reviewer)
**Orchestrator**: Antigravity
**Status**: 🟢 APPROVE

---

## 🔍 Summary
이번 PR은 GodMode 대시보드의 "Scenario Progress & KPI Visualizers"와 이를 지원하기 위한 "On-Demand Telemetry (Pull Model)" 시스템을 구현합니다. UI 컴포넌트의 요구사항에 따라 실시간으로 데이터 마스킹을 조정하여 대역폭 효율성을 극대화한 설계가 돋보입니다.

---

## 🚨 Critical Issues
- **발견된 심각한 보안 위반이나 하드코딩된 Secret이 없습니다.**

---

## ⚠️ Logic & Spec Gaps
### 1. Manual Enum Mapping (Brittle Logic)
`dashboard/components/main_cockpit.py` (Line 123-128)에서 WebSocket으로 받은 문자열을 `ScenarioStatus` Enum으로 수동 매핑하고 있습니다.
- **Risk**: `ScenarioStatus`에 새로운 상태가 추가될 경우 UI 코드를 수동으로 업데이트해야 하며, 누락 시 `PENDING`으로 오작동할 수 있습니다.
- **Action**: DTO 내부에 `from_dict` 메서드를 구현하거나, `ScenarioStatus(status_str)`와 같이 Enum 생성자를 직접 사용하도록 리팩토링을 권장합니다.

---

## 💡 Suggestions
### 1. Performance Optimization for Heatmaps
`AgentHeatmapVisualizer`에서 수천 명의 에이전트를 Plotly Scatter로 렌더링할 경우 Streamlit UI가 무거워질 수 있습니다.
- **Suggestion**: 에이전트 수가 많아질 경우 `plotly.graph_objects.Scattergl` (WebGL 기반) 사용을 검토하거나, 백엔드에서 미리 히스토그램으로 집계(Aggregation)하여 전달하는 방식을 고려하십시오.

### 2. Serialization Library Usage
Jules가 Insight에서 언급한 대로, 수동으로 DTO를 재구성하는 대신 `pydantic`이나 `dacite` 같은 라이브러리를 사용하면 코드가 더 견고해지고 타입 안정성이 높아집니다.

---

## 🧠 Implementation Insight Evaluation
- **Original Insight**: `communications/insights/mission-ui-03.md`에 기록됨. "Pull Model" 아키텍처와 `UPDATE_TELEMETRY` 명령을 통한 동적 구독 관리의 정당성을 잘 설명하고 있음.
- **Reviewer Evaluation**: 
    - **Excellent**: UI가 필요한 데이터(Required Mask)를 선언하고 시스템이 이에 응답하는 방식은 분산 시스템에서 매우 효율적인 전략입니다.
    - **Accuracy**: WebSocket 연동 포인트 미비에 대한 솔직한 기술 부채 기록은 아키텍트가 후속 작업을 계획하는 데 매우 유용합니다.

---

## 📚 Manual Update Proposal (Draft)
- **Target File**: `design/2_operations/ledgers/ECONOMIC_INSIGHTS.md` (또는 `TELEMETRY_STANDARDS.md`)
- **Draft Content**:
    ```markdown
    ### [2026-02-13] On-Demand Telemetry "Pull Model" 적용
    - **Context**: 마이크로 데이터(에이전트 상세 스탯)는 전송량이 커서 상시 브로드캐스트가 부적절함.
    - **Solution**: UI 컴포넌트가 `required_mask`를 소유하고, 활성화 시 `UPDATE_TELEMETRY` 명령을 Simulation에 전송하는 'Pull Model' 구현.
    - **Impact**: 필요한 시점에만 상세 데이터를 수집하므로 네트워크 부하 감소 및 대시보드 확장성 확보.
    - **Guideline**: 새로운 시각화 도구 추가 시 `BaseVisualizer`를 상속받아 `required_mask`를 정의할 것.
    ```

---

## ✅ Verdict
- **Verdict**: **APPROVE**
- **Reason**: 
    - 보안 위반 없음.
    - **인사이트 보고서(`communications/insights/mission-ui-03.md`)가 PR에 포함되어 있음.**
    - 통합 테스트(`tests/integration/test_telemetry_pipeline.py`)를 통해 핵심 로직인 동적 마스킹 업데이트가 검증됨.
    - 아키텍처 설계(Pull Model)가 프로젝트의 확장성 방향과 일치함.