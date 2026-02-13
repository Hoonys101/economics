# 🐙 Code Review Report: Mission INT-01 Integration

**🔍 Summary**: WebSocket 기반의 Watchtower V2 서버를 통합하고, 시뮬레이션 엔진의 Phase 0(Intercept) 및 Phase 8(Scenario Analysis)에 연결했습니다. 또한 Integer Pennies 마이그레이션으로 인한 누락된 필드 참조(wage, valuation 등)를 전수 조사하여 수정했습니다.

---

### 🚨 Critical Issues
*   **보안 및 하드코딩 (Security)**: 발견된 심각한 보안 위반 사항은 없습니다. WebSocket 포트(8765)와 호스트(0.0.0.0)는 `scripts/run_watchtower.py`에서 정의되어 외부 노출 시 관리가 필요하나, 내부 테스트 용도로는 허용 범위입니다.

### ⚠️ Logic & Spec Gaps
1.  **Stateless Engine Purity 위반 (`simulation/ai/firm_ai.py`)**: 
    *   `FirmAI.process` (추정) 메서드 내부에서 `firm_agent` 객체를 직접 인자로 받아 `firm_agent.prev_awareness = current_awareness`와 같이 상태를 직접 수정하고 있습니다.
    *   **Violation**: "Engine이 Agent 핸들을 직접 참조하지 말아야 하며, 모든 상태 변경은 Agent 내에서만 일어나야 한다"는 아키텍처 원칙을 위반합니다. 엔진은 결정(Decision) DTO만 반환하고, 에이전트가 이를 적용하는 구조로 리팩토링이 필요합니다.
2.  **비효율적인 객체 생성 (`simulation/orchestration/phases/scenario_analysis.py`)**:
    *   매 틱(Tick)마다 실행되는 `Phase_ScenarioAnalysis` 내부에서 `DashboardService(self.world_state)`를 매번 인스턴스화하고 있습니다.
    *   **Impact**: `DashboardService`는 내부적으로 `PersistenceBridge` 등 무거운 컴포넌트를 생성하므로, 매 틱마다 생성하는 것은 불필요한 GC 부하와 자원 낭비를 초래합니다. `WorldState`에 서비스 인스턴스를 캐싱하여 재사용하십시오.
3.  **의존성 주입 위반 (`simulation/world_state.py`)**:
    *   `GlobalRegistry`를 `modules.system.registry`에서 직접 import하여 생성하고 있습니다. 이는 인터페이스(`api.py`)를 통한 통신 원칙에 어긋나며, `modules/system/api.py`에서 제공하는 팩토리나 프로토콜을 사용해야 합니다.

### 💡 Suggestions
*   **Config 활용**: `scripts/run_watchtower.py`의 `HOST`, `PORT`를 `config/simulation.yaml`로 이관하여 설정 중앙화를 구현하십시오.
*   **Lazy Loading**: `Phase0_Intercept`에서 `CommandService`를 lazy하게 생성하는 방식(`_ensure_service_initialized`)은 좋으나, 가급적 Orchestrator 레벨에서 준비된 서비스를 주입받는 것이 테스트 용이성 측면에서 더 유리합니다.

### 🧠 Implementation Insight Evaluation
*   **Original Insight**: Jules는 `Bridge Pattern`을 사용해 엔진과 서버를 격리하고, `Integer Pennies` 마이그레이션 누락 건들을 정확히 짚어내어 수정했습니다. 특히 `LaborManager`와 `StockTracker`의 데이터 타입 불일치 해결은 칭찬할 만한 디테일입니다.
*   **Reviewer Evaluation**: 통찰력이 매우 구체적이며 실제 발생한 버그 수정 내용이 논리적입니다. 다만, "Stateless Engine"에 대한 엄격한 준수가 누락된 점은 기술 부채로 기록되어야 합니다.

### 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/1_governance/architecture/standards/ENGINE_PURITY.md`
*   **Draft Content**:
    ```markdown
    ### [Case Study] AI Engine State Modification
    - **Anti-Pattern**: Engine 직접 수정 (`agent.attribute = value`)
    - **Standard**: Engine은 오직 데이터(DTO)를 읽고 결과(DTO)를 반환한다.
    - **Refactoring Example**: 
        - Before: `engine.process(agent) -> agent.state = new_state`
        - After: `decision = engine.decide(agent_snapshot) -> return ActionDTO(new_state)`
    ```

---

### ✅ Verdict: **REQUEST CHANGES (Hard-Fail)**

**이유**:
1.  **Engine Purity**: `FirmAI`에서 Agent 객체를 직접 조작하는 로직은 시스템 확장성을 저해하므로 수정이 필수적입니다.
2.  **Performance Hygiene**: Phase 8에서 `DashboardService`를 매 틱마다 생성하는 비효율적인 로직의 수정이 필요합니다.
3.  **Dependency**: `WorldState` 내의 구체 클래스(`GlobalRegistry`) 직접 생성을 `api.py` 패턴으로 변경하십시오.