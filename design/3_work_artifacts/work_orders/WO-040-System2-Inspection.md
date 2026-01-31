# Work Order: - System 2 Inspection (The Why)

## Phase: 20.5 Step 4 (Parallel Track C)

## Objective
개별 에이전트의 System 2(Planner)가 내린 의사결정의 근거를 들여다봅니다.

---

## Implementation Specs

### 1. Agent Selector (Sidebar)
- `st.sidebar.number_input("Agent ID", min_value=0, max_value=...)` 추가.
- 선택된 ID를 `st.session_state['selected_agent_id']`에 저장.

### 2. Inspector Panel (Main Area)
- `st.expander("🧠 Agent Mind Inspector")` 배치.
- 선택된 에이전트의 상세 정보 표시.

### 3. Data Exposure
| Field | Source |
|---|---|
| **Current Assets** | `agent.assets` |
| **Projected NPV** | `agent.system2_planner.cached_projection['npv_wealth']` |
| **Bankruptcy Risk** | `agent.system2_planner.cached_projection['bankruptcy_tick']` |
| **Last Decision** | Custom log field (if available) |

### 4. Connector Integration
```python
# dashboard_connector.py
def get_agent_details(simulation: Simulation, agent_id: int) -> Dict[str, Any]:
 """Returns detailed info for a specific agent."""
 agent = simulation.agents.get(agent_id)
 if not agent:
 return {"error": "Agent not found"}

 system2 = getattr(agent, 'system2_planner', None)
 projection = system2.cached_projection if system2 else {}

 return {
 "id": agent.id,
 "assets": agent.assets,
 "is_active": agent.is_active,
 "gender": getattr(agent, 'gender', 'N/A'),
 "age": getattr(agent, 'age', 0),
 "children_count": len(getattr(agent, 'children_ids', [])),
 "npv_wealth": projection.get("npv_wealth", 0.0),
 "bankruptcy_tick": projection.get("bankruptcy_tick", None),
 }
```

---

## Files to Modify
1. **`dashboard/app.py`**: Add agent selector and inspector panel.
2. **`simulation/interface/dashboard_connector.py`**: Add `get_agent_details()` method.

---

## Verification
- Select an agent ID in the sidebar.
- Confirm Inspector panel shows correct data for that agent.
- Run a few ticks and verify NPV updates.

## Deliverable
- PR to main with working agent inspector.
