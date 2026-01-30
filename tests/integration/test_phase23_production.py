import pytest
from unittest.mock import MagicMock
from simulation.components.production_department import ProductionDepartment
from simulation.systems.technology_manager import TechnologyManager
from simulation.firms import Firm

class TestPhase23Production:
    @pytest.fixture
    def config(self):
        mock_config = MagicMock()
        # Use lower-case attributes to match FirmConfigDTO usage in ProductionDepartment
        mock_config.labor_alpha = 0.5
        mock_config.labor_elasticity_min = 0.1
        mock_config.automation_labor_reduction = 0.0
        mock_config.capital_depreciation_rate = 0.0
        # Mock GOODS structure
        mock_config.goods = {"food": {"sector": "FOOD"}}
        # Tech manager might still expect upper case for global economy params if it uses config_module
        # But ProductionDepartment uses FirmConfigDTO which is lowercase.
        # Let's set both just in case TechManager uses this same mock object differently.
        mock_config.TECH_FERTILIZER_UNLOCK_TICK = 0
        mock_config.TECH_DIFFUSION_RATE = 0.0
        # Fix: Ensure multiplier is a float, not a Mock, because MagicMock attributes always exist
        mock_config.TECH_FERTILIZER_MULTIPLIER = 3.0
        mock_config.TECH_UNLOCK_COST_THRESHOLD = 5000.0
        mock_config.TECH_UNLOCK_PROB_CAP = 0.1
        return mock_config

    @pytest.fixture
    def firm_setup(self, config):
        def _create_firm(firm_id):
            firm = MagicMock(spec=Firm)
            firm.id = firm_id
            firm.sector = "FOOD"
            firm.specialization = "food"
            firm.is_visionary = False
            firm.productivity_factor = 1.0
            firm.capital_stock = 100.0
            firm.automation_level = 0.0
            firm.base_quality = 1.0
            firm.inventory = {}
            firm.input_inventory = {}
            firm.hr = MagicMock()
            firm.hr.employees = [MagicMock()] # At least one employee
            firm.hr.get_total_labor_skill.return_value = 100.0
            firm.hr.get_avg_skill.return_value = 1.0

            # Create real ProductionDepartment for the mock firm
            firm.production_department = ProductionDepartment(firm, config)
            # Inject production department back into firm.production if needed by other components,
            # but here we test production_department directly or via produce

            # Add inventory method
            firm.add_inventory = MagicMock()

            return firm, firm.production_department
        return _create_firm

    def test_production_boost_from_fertilizer_tech(self, config, firm_setup):
        # 1. Create two identical firms
        firm_A, prod_A = firm_setup(1)
        firm_B, prod_B = firm_setup(2)

        # 2. Create TechnologyManager and unlock Tech
        tech_manager = TechnologyManager(config, MagicMock())
        tech_node = tech_manager.tech_tree["TECH_AGRI_CHEM_01"]
        tech_node.is_unlocked = True
        tech_manager.active_techs.append(tech_node.id)

        # 3. Manually have firm_A adopt the tech
        tech_manager._adopt(firm_A.id, tech_node)

        # 4. Run produce
        # Note: ProductionDepartment.produce returns quantity

        qty_A = prod_A.produce(10, tech_manager)
        qty_B = prod_B.produce(10, tech_manager)

        # 5. Assert production_A is approx 3.0 * production_B
        assert qty_B > 0
        ratio = qty_A / qty_B
        print(f"Production A: {qty_A}, Production B: {qty_B}, Ratio: {ratio}")

        # Tech multiplier is 3.0.
        assert abs(ratio - 3.0) < 0.01
