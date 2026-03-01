import pytest
from unittest.mock import MagicMock
from simulation.firms import Firm
from simulation.core_agents import Household
from modules.simulation.api import AgentStateDTO, InventorySlot, AgentCoreConfigDTO
from simulation.ai.enums import Personality

class TestSerialization:
    def test_firm_multi_inventory_save_load(self):
        # 1. Setup Firm
        core_config = AgentCoreConfigDTO(
            id=1, name="Firm_1", value_orientation="PROFIT",
            initial_needs={}, logger=MagicMock(), memory_interface=None
        )
        decision_engine = MagicMock()

        # Mock Config DTO
        config_dto = MagicMock()
        config_dto.firm_min_production_target = 10.0
        config_dto.ipo_initial_shares = 1000
        config_dto.dividend_rate = 0.1
        config_dto.profit_history_ticks = 10
        config_dto.goods = {}
        config_dto.fire_sale_discount = 0.5
        config_dto.initial_firm_assets = 1000

        firm = Firm(
            core_config=core_config,
            engine=decision_engine,
            specialization="A",
            productivity_factor=1.0,
            config_dto=config_dto
        )

        # 2. Add Items
        from simulation.systems.settlement_system import InventorySentry
        with InventorySentry.unlocked():
            firm.add_item("item_main", 10.0, slot=InventorySlot.MAIN)
            firm.add_item("item_input", 5.0, slot=InventorySlot.INPUT)

        # 3. Get State
        state_dto = firm.get_current_state()

        # Assert DTO structure
        assert state_dto.inventories[InventorySlot.MAIN.name].items[0].name == "item_main"
        assert state_dto.inventories[InventorySlot.INPUT.name].items[0].name == "item_input"

        # 4. Load State into new Firm
        new_firm = Firm(
            core_config=core_config,
            engine=decision_engine,
            specialization="A",
            productivity_factor=1.0,
            config_dto=config_dto
        )
        new_firm.load_state(state_dto)

        # 5. Verify
        assert new_firm.get_quantity("item_main", slot=InventorySlot.MAIN) == 10.0
        assert new_firm.get_quantity("item_input", slot=InventorySlot.INPUT) == 5.0
        assert new_firm.get_quantity("item_main", slot=InventorySlot.INPUT) == 0.0

    def test_household_multi_inventory_save_load(self):
         # 1. Setup Household
        core_config = AgentCoreConfigDTO(
            id=2, name="Household_2", value_orientation="BALANCED",
            initial_needs={}, logger=MagicMock(), memory_interface=None
        )
        decision_engine = MagicMock()

        # Mock Config DTO
        config_dto = MagicMock()
        config_dto.initial_household_age_range = (20, 30)
        config_dto.price_memory_length = 10
        config_dto.wage_memory_length = 10
        config_dto.ticks_per_year = 365
        config_dto.adaptation_rate_normal = 0.1
        config_dto.initial_aptitude_distribution = (0.5, 0.1)
        config_dto.value_orientation_mapping = {}
        config_dto.conformity_ranges = {}
        config_dto.initial_household_assets_mean = 1000
        config_dto.quality_pref_snob_min = 0.8
        config_dto.quality_pref_miser_max = 0.2

        talent = MagicMock()

        household = Household(
            core_config=core_config,
            engine=decision_engine,
            talent=talent,
            goods_data=[],
            personality=Personality.BALANCED,
            config_dto=config_dto
        )

        # 2. Add Items
        household.add_item("item_main", 10.0, slot=InventorySlot.MAIN)

        # 3. Get State
        state_dto = household.get_current_state()

        # Assert DTO structure
        assert state_dto.inventories[InventorySlot.MAIN.name].items[0].name == "item_main"

        # 4. Load State into new Household
        new_household = Household(
            core_config=core_config,
            engine=decision_engine,
            talent=talent,
            goods_data=[],
            personality=Personality.BALANCED,
            config_dto=config_dto
        )
        new_household.load_state(state_dto)

        # 5. Verify
        assert new_household.get_quantity("item_main", slot=InventorySlot.MAIN) == 10.0
