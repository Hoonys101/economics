from unittest.mock import call as call

class TestSimulationInitializer:
    def test_registry_linked_before_bootstrap(self, MockAgentRegistry, MockBootstrapper, MockSettlementSystem, MockSimulation, MockLockManager) -> None: ...
