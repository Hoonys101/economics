from dataclasses import dataclass, field

@dataclass
class MockAIConfig:
    decision_cycle: int = 10
    max_memory_entries: int = 100
    pruning_threshold: float = 0.5

@dataclass
class MockEconomyConfig:
    starting_population: int = 50
    goods: list[str] = field(default_factory=lambda: ["food", "wood", "tools"])

@dataclass
class MockMarketConfig:
    initial_prices: dict[str, float] = field(default_factory=lambda: {"food": 1.0, "wood": 2.0})
    enable_dynamic_pricing: bool = False

@dataclass
class MockSimulationConfig:
    """
    A standardized, mockable configuration object for testing
    AI engines and other simulation components in isolation.
    """
    ai: MockAIConfig = field(default_factory=MockAIConfig)
    economy: MockEconomyConfig = field(default_factory=MockEconomyConfig)
    market: MockMarketConfig = field(default_factory=MockMarketConfig)
    simulation_id: str = "mock_sim_001"
    total_ticks: int = 1000
