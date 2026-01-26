# Spec: WO-121 Feedback Integration

**Objective:** Address the feedback from the PR review for WO-121 (`Fix Newborn Initialization`) to improve code quality, adhere to the "Single Source of Truth" principle, and make the testing ecosystem more robust.

---

## 1. 🚨 Risk & Impact Audit (Mandatory Review)

Before implementation, review the following architectural constraints identified in the pre-flight audit. Failure to adhere to these will result in rework.

-   **God Class Dependency**: The `process_births` method is tightly coupled to the `Simulation` engine object. **Do not** attempt to refactor this dependency. Your implementation must assume it receives the `simulation: Any` object and its various attributes (`.ai_trainer`, `.markets`, etc.).
-   **Surgical Precision Required**: The method is a complex factory. Your changes **must be confined to the `initial_needs` logic only**. Do not alter asset gifting, talent inheritance, or other parts of the agent creation process.
-   **Test Mocking Strategy**: Existing tests are brittle. The refactored tests **must mock the configuration system and the `simulation` object's attributes** to achieve true unit testing. You will not instantiate a full `Simulation` engine.
-   **Circular Dependency Avoidance**: Do not add new module-level imports that could create import cycles. Respect the existing pattern of passing engine instances at runtime.

---

## 2. Configuration (`config/economy_params.yaml`)

Externalize the initial needs configuration from the Python codebase to the YAML configuration file. This ensures that economic parameters are centralized and managed outside of application logic.

**Action:** Add the following section to `config/economy_params.yaml`.

```yaml
# ----------------------------------------------------------------------
# Demographics & Household Configuration
# ----------------------------------------------------------------------
NEWBORN_INITIAL_NEEDS:
  # Basic physiological needs to ensure survival and initial action.
  # Values represent the starting level of the need.
  food: 50.0
  health: 80.0
  shelter: 20.0 # Assumes initial period with parents
```

---

## 3. Logic Refactoring (`simulation/systems/demographic_manager.py`)

Refactor `DemographicManager.process_births` to use the new configuration from `economy_params.yaml` as the **Single Source of Truth** for a newborn's initial needs.

**Action:**
1.  Remove any local, hardcoded `default_needs` dictionary within the `process_births` method.
2.  Modify the `Household` instantiation to pass needs loaded from the configuration module.

**Pseudo-code:**

```python
# In simulation/systems/demographic_manager.py

class DemographicManager:
    # ...

    def process_births(
        self,
        simulation: Any,
        birth_requests: List[Household]
    ) -> List[Household]:
        """
        Executes birth requests.
        Creates new Household agents, inherits traits, sets up lineage.
        """
        new_children = []
        
        # 1. Load the initial needs from the config module.
        #    The config loader is responsible for providing this attribute.
        #    Use an empty dict as a safe fallback.
        initial_needs_for_newborn = getattr(self.config_module, "NEWBORN_INITIAL_NEEDS", {})
        if not initial_needs_for_newborn:
            self.logger.warning(
                "NEWBORN_INITIAL_NEEDS not found in config. Newborns may be inactive."
            )

        for parent in birth_requests:
            # ... (existing logic for ID generation, asset transfer, etc.)

            # 2. When creating the child, pass the loaded initial needs.
            #    Remove any hardcoded or local default dictionaries.
            child = Household(
                id=child_id,
                # ... (other parameters)
                initial_needs=initial_needs_for_newborn.copy(), # Use .copy() to prevent shared state
                # ... (other parameters)
            )

            # ... (existing logic for lineage, logging, etc.)

            new_children.append(child)

        return new_children

    # ...
```

---

## 4. Test Refactoring (`tests/systems/test_demographic_manager_newborn.py`)

Create or refactor the test file to verify the new logic in a robust and isolated manner. The test must not depend on a full `Simulation` instance or the real `config.py`.

**File:** `tests/systems/test_demographic_manager_newborn.py`

**Key Strategy:**
-   Use `pytest` fixtures and `unittest.mock.MagicMock` to create stand-ins for `DemographicManager`'s dependencies.
-   Directly patch the `config_module` attribute of the `DemographicManager` instance during the test.

**Implementation Plan:**

```python
import pytest
from unittest.mock import MagicMock, PropertyMock

from simulation.systems.demographic_manager import DemographicManager
from simulation.core_agents import Household

# [Test File Start]

@pytest.fixture
def mock_config():
    """Fixture to create a mock config object for testing."""
    config = MagicMock()
    
    # Define the expected config value for this test
    config.NEWBORN_INITIAL_NEEDS = {"food": 100.0, "test_need": 50.0}
    
    # Mock other required config values
    config.REPRODUCTION_AGE_START = 20
    config.REPRODUCTION_AGE_END = 45
    
    return config

@pytest.fixture
def mock_simulation():
    """Fixture to create a mock simulation 'God Object'."""
    sim = MagicMock()
    
    # Mock all attributes accessed by process_births
    sim.next_agent_id = 101
    sim.time = 1000
    sim.logger = MagicMock()
    
    # Mock dependent systems
    sim.ai_trainer = MagicMock()
    sim.ai_trainer.get_engine.return_value = MagicMock()
    sim.markets = {"loan_market": MagicMock()}
    sim.goods_data = {} # Assuming this is sufficient
    
    # Mock the AI Training Manager for brain inheritance
    type(sim).ai_training_manager = PropertyMock(return_value=MagicMock())

    return sim

@pytest.fixture
def parent_agent(mock_config):
    """Fixture for a parent Household agent ready to give birth."""
    parent = MagicMock(spec=Household)
    parent.id = 1
    parent.age = 30
    parent.assets = 1000.0
    parent.talent = MagicMock()
    parent.personality = "STABLE"
    parent.value_orientation = "TRADITIONAL"
    parent.risk_aversion = 0.5
    parent.generation = 1
    parent.children_ids = []
    
    # Mock methods
    parent._sub_assets.return_value = None
    
    return parent

def test_newborn_receives_initial_needs_from_config(mock_config, mock_simulation, parent_agent):
    """
    VERIFY: A newborn household is initialized with 'initial_needs' from the 
            mocked config, not a hardcoded default.
    """
    # ARRANGE
    # Instantiate the manager and surgically attach the mock config
    manager = DemographicManager(config_module=mock_config)
    manager.logger = MagicMock() # Isolate logger

    birth_requests = [parent_agent]

    # ACT
    # This now uses a completely mocked ecosystem
    new_children = manager.process_births(mock_simulation, birth_requests)

    # ASSERT
    assert len(new_children) == 1
    child = new_children[0]
    
    # The CRITICAL check: are the needs from our mock_config?
    assert child.needs == mock_config.NEWBORN_INITIAL_NEEDS
    assert "food" in child.needs
    assert "test_need" in child.needs
    assert child.needs["food"] == 100.0
    
    # Verify other attributes were set correctly
    assert child.id == 101
    assert child.parent_id == parent_agent.id
    assert child.age == 0.0
    
    # Verify asset transfer happened
    parent_agent._sub_assets.assert_called_once_with(parent_agent.assets * 0.1)
```

---

## 5. Documentation Update (`AGENTS.md`)

To capture the lesson learned from the original bug, propose the following update. This formalizes the principle that all agents must be born with intrinsic motivation.

**Action:** Add the following principle to `AGENTS.md` under a relevant section (e.g., "Agent Lifecycle Principles").

```markdown
### Principle: All Agents are Born with Purpose (Initial Needs)

-   **Phenomenon**: Newborn agents were created but remained inactive, eventually being culled by the simulation for failing to act.
-   **Cause**: Agents were initialized with an empty `initial_needs` dictionary (`{}`). The decision-making engine had no unmet needs to address, resulting in a permanent state of inaction (apathy).
-   **Solution**: A default set of `NEWBORN_INITIAL_NEEDS` (e.g., for food, health) is now defined in `config/economy_params.yaml`. The `DemographicManager` injects these needs upon agent creation, providing an immediate set of goals.
-   **Lesson**: An agent's existence requires not just physical attributes but also **intrinsic motivation**. Every agent must be initialized with a non-empty set of needs that drives their first actions. Without a goal, an agent is inert.
```

---
## 6. 📝 Mandatory Reporting

**Jules:** Upon completion, document any insights or newly discovered technical debt in the `communications/insights/` directory. Specifically, report on the ease or difficulty of mocking the `Simulation` object during testing, as this may inform future refactoring efforts.
