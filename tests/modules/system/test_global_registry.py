import pytest
from modules.system.registry import GlobalRegistry
from modules.system.api import OriginType, RegistryValueDTO
from simulation.dtos.watchtower import WatchtowerSnapshotDTO, IntegrityDTO, MacroDTO, FinanceDTO, FinanceRatesDTO, FinanceSupplyDTO, PoliticsDTO, PoliticsApprovalDTO, PoliticsStatusDTO, PoliticsFiscalDTO, PopulationDTO, PopulationDistributionDTO, PopulationMetricsDTO
from modules.governance.cockpit.api import CockpitCommand

class TestGlobalRegistry:
    def test_basic_set_get(self):
        registry = GlobalRegistry()
        registry.set("test.key", 100, OriginType.SYSTEM)
        assert registry.get("test.key") == 100

        # Override with higher priority
        registry.set("test.key", 200, OriginType.CONFIG)
        assert registry.get("test.key") == 200

        # Ignored update from lower priority
        registry.set("test.key", 150, OriginType.SYSTEM)
        assert registry.get("test.key") == 200

    def test_locking_mechanism(self):
        registry = GlobalRegistry()
        registry.set("locked.key", "initial", OriginType.CONFIG)

        # Lock via God Mode
        registry.lock("locked.key")
        entry = registry.get_entry("locked.key")
        assert entry.is_locked
        assert entry.origin == OriginType.GOD_MODE

        # Attempt update from USER (lower than GOD)
        with pytest.raises(PermissionError):
            registry.set("locked.key", "hacked", OriginType.USER)

        # Unlock
        registry.unlock("locked.key")
        # After unlock, the GOD_MODE layer is removed, revealing CONFIG layer
        assert registry.get("locked.key") == "initial"

        # Now USER can update
        registry.set("locked.key", "updated", OriginType.USER)
        assert registry.get("locked.key") == "updated"

    def test_migrate_from_dict(self):
        data = {
            "economy.inflation_target": 0.02,
            "sim.ticks_per_year": 100
        }
        registry = GlobalRegistry(initial_data=data)

        assert registry.get("economy.inflation_target") == 0.02
        assert registry.get("sim.ticks_per_year") == 100

        entry = registry.get_entry("economy.inflation_target")
        assert entry.origin == OriginType.CONFIG
        assert entry.domain == "economy"

    def test_reset_to_defaults(self):
        registry = GlobalRegistry()
        registry.set("param", 10, OriginType.SYSTEM)
        registry.set("param", 20, OriginType.USER)

        assert registry.get("param") == 20

        registry.reset_to_defaults()
        assert registry.get("param") == 10

        entry = registry.get_entry("param")
        assert entry.origin == OriginType.SYSTEM

    def test_delete_layer(self):
        registry = GlobalRegistry()
        registry.set("param", 1, OriginType.SYSTEM)
        registry.set("param", 2, OriginType.CONFIG)
        registry.set("param", 3, OriginType.USER)

        assert registry.get("param") == 3

        registry.delete_layer("param", OriginType.USER)
        assert registry.get("param") == 2

        registry.delete_layer("param", OriginType.CONFIG)
        assert registry.get("param") == 1

    def test_snapshot_returns_pydantic(self):
        registry = GlobalRegistry()
        registry.set("key1", "val1")

        snapshot = registry.snapshot()
        assert "key1" in snapshot
        assert isinstance(snapshot["key1"], RegistryValueDTO)
        assert snapshot["key1"].value == "val1"

    def test_watchtower_dto_serialization(self):
        # Verify WatchtowerSnapshotDTO serialization (for server.py)
        dto = WatchtowerSnapshotDTO(
            tick=1,
            timestamp=1234567890.0,
            status="RUNNING",
            integrity=IntegrityDTO(m2_leak=0, fps=60.0),
            macro=MacroDTO(gdp=1000, cpi=1.0, unemploy=0.05, gini=0.3),
            finance=FinanceDTO(
                rates=FinanceRatesDTO(base=0.02, call=0.02, loan=0.05, savings=0.01),
                supply=FinanceSupplyDTO(m0=100, m1=200, m2=300, velocity=1.5)
            ),
            politics=PoliticsDTO(
                approval=PoliticsApprovalDTO(total=0.5, low=0.4, mid=0.5, high=0.6),
                status=PoliticsStatusDTO(ruling_party="TestParty", cohesion=0.8),
                fiscal=PoliticsFiscalDTO(revenue=1000, welfare=100, debt=5000)
            ),
            population=PopulationDTO(
                distribution=PopulationDistributionDTO(q1=10.0, q2=20.0, q3=30.0, q4=40.0, q5=50.0),
                active_count=100,
                metrics=PopulationMetricsDTO(birth=0.01, death=0.01)
            )
        )

        # Test model_dump
        data = dto.model_dump()
        assert data["tick"] == 1
        assert data["integrity"]["m2_leak"] == 0
        assert data["macro"]["gdp"] == 1000

    def test_cockpit_command_validation(self):
        # Test valid command
        raw_data = {"type": "PAUSE", "payload": {}}
        cmd = CockpitCommand.model_validate(raw_data)
        assert cmd.type == "PAUSE"
        assert cmd.payload == {}

        # Test invalid command (missing type)
        with pytest.raises(ValueError):
             CockpitCommand.model_validate({"payload": {}})

        # Test invalid command (wrong type)
        with pytest.raises(ValueError):
             CockpitCommand.model_validate({"type": "INVALID", "payload": {}})
