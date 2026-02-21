# AUDIT_REPORT_STRUCTURAL

## God Classes (>800 lines)
- **Firm** in `simulation/firms.py`: 1388 lines
- **Household** in `simulation/core_agents.py`: 1039 lines

## Leaky Abstractions
None found.

## Potential Constructor Leaks
- Attribute _state_container initialized with self passed as arg in `simulation/core_agents.py`
- Attribute infrastructure_manager initialized with self passed as arg in `simulation/agents/government.py`
