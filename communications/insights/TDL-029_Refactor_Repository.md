# TDL-029: Refactor SimulationRepository to Unit of Work Pattern

## 1. Background
The `SimulationRepository` class (`simulation/db/repository.py`) was acting as a "God Class" facade, wrapping every method from its sub-repositories (`AgentRepository`, `MarketRepository`, `AnalyticsRepository`, `RunRepository`). This resulted in a monolithic interface with over 20 methods, violating the Single Responsibility Principle and Interface Segregation Principle.

## 2. Refactoring Execution
- **Unit of Work Pattern**: `SimulationRepository` has been refactored to serve as a container (Unit of Work) that initializes and exposes specific repositories as public attributes (`.agents`, `.markets`, `.analytics`, `.runs`).
- **Facade Removal**: All wrapper methods (e.g., `save_transaction`, `get_agent_states`) were removed.
- **Consumer Updates**: All consumers (ViewModels, PersistenceManager, Engine, etc.) were updated to access the specific sub-repository directly (e.g., `repo.agents.get_agent_states(...)`).
- **Test Updates**: Unit tests in `tests/unit/test_repository.py` were updated to reflect the new API.

## 3. Discovered Technical Debt

### 3.1. ViewModel Dependency Injection
Many ViewModels (e.g., `AgentStateViewModel`) have a default argument `repository=None` in `__init__`, which defaults to instantiating a *new* `SimulationRepository`.
```python
def __init__(self, repository: Optional[SimulationRepository] = None):
    self.repository = repository if repository else SimulationRepository()
```
**Risk**: This creates hidden dependencies and makes unit testing harder because it requires mocking the `SimulationRepository` constructor or the database connection. Ideally, the repository should always be injected, or retrieved from a Service Locator / Dependency Injection Container.

### 3.2. Test Environment Dependencies
Running the full test suite (`python -m pytest`) revealed missing dependencies in the environment:
- `python-dotenv`
- `joblib`
- `requests`
- `numpy` (was missing, installed during verification)

These should be added to `requirements.txt` to ensure a consistent development environment.

### 3.3. PersistenceManager Coupling
`PersistenceManager` is coupled to `SimulationRepository`. While improved by accessing specific sub-repos, it still depends on the concrete `SimulationRepository` class.

## 4. Future Recommendations
- **Enforce Dependency Injection**: Remove the default `SimulationRepository()` instantiation in ViewModels. Force the caller to provide the repository instance.
- **Update requirements.txt**: Add the missing dependencies found during testing.
- **Type Hinting**: Ensure all sub-repositories are properly type-hinted in `SimulationRepository` for better IDE support.
