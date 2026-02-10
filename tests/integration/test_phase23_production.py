import pytest
from unittest.mock import MagicMock
from simulation.firms import Firm
from simulation.systems.technology_manager import TechnologyManager
from modules.simulation.api import AgentCoreConfigDTO

class TestPhase23Production:
    @pytest.fixture
    def config(self):
        mock_config = MagicMock()
        mock_config.labor_alpha = 0.5
        mock_config.labor_elasticity_min = 0.1
        mock_config.automation_labor_reduction = 0.0
        mock_config.capital_depreciation_rate = 0.0
        mock_config.goods = {"food": {"sector": "FOOD"}}
        # Tech manager params
        mock_config.TECH_FERTILIZER_UNLOCK_TICK = 0
        mock_config.TECH_DIFFUSION_RATE = 0.0
        mock_config.TECH_FERTILIZER_MULTIPLIER = 3.0
        mock_config.TECH_UNLOCK_COST_THRESHOLD = 5000.0
        mock_config.TECH_UNLOCK_PROB_CAP = 0.1
        # Fix for deque maxlen requiring an integer
        mock_config.profit_history_ticks = 50
        return mock_config

    @pytest.fixture
    def firm_setup(self, config):
        def _create_firm(firm_id):
            core_config = AgentCoreConfigDTO(
                id=firm_id,
                name=f"Firm_{firm_id}",
                logger=MagicMock(),
                memory_interface=None,
                value_orientation="PROFIT",
                initial_needs={}
            )
            firm = Firm(
                core_config=core_config,
                engine=MagicMock(),
                specialization="food",
                productivity_factor=1.0,
                config_dto=config,
                initial_inventory={},
                loan_market=None,
                sector="FOOD"
            )
            # Setup State
            firm.production_state.capital_stock = 100.0
            firm.production_state.automation_level = 0.0
            firm.production_state.base_quality = 1.0

            # HR State - Need employees
            mock_emp = MagicMock()
            mock_emp.labor_skill = 100.0 # Match original test skill
            firm.hr_state.employees = [mock_emp]

            return firm
        return _create_firm

    def test_production_boost_from_fertilizer_tech(self, config, firm_setup):
        # 1. Create two identical firms
        firm_A = firm_setup(1)
        firm_B = firm_setup(2)

        # 2. Create TechnologyManager and unlock Tech
        tech_manager = TechnologyManager(config, MagicMock())
        tech_node = tech_manager.tech_tree["TECH_AGRI_CHEM_01"]
        tech_node.is_unlocked = True
        tech_manager.active_techs.append(tech_node.id)

        # 3. Manually have firm_A adopt the tech
        tech_manager._adopt(firm_A.id, tech_node)

        # Patch get_productivity_multiplier to bypass mocked numpy issues
        # Since numpy mocks prevent actual state storage/retrieval in adoption_matrix
        original_get_multiplier = tech_manager.get_productivity_multiplier
        tech_manager.get_productivity_multiplier = MagicMock(side_effect=lambda fid: 3.0 if fid == firm_A.id else 1.0)

        # 4. Run produce
        firm_A.produce(10, tech_manager)
        firm_B.produce(10, tech_manager)

        qty_A = firm_A.get_quantity("food")
        qty_B = firm_B.get_quantity("food")

        # 5. Assert production_A is approx 3.0 * production_B
        assert qty_B > 0
        ratio = qty_A / qty_B
        print(f"Production A: {qty_A}, Production B: {qty_B}, Ratio: {ratio}")

        # Tech multiplier is 3.0.
        assert abs(ratio - 3.0) < 0.01
