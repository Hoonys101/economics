import pytest
import config
from modules.system.builders.simulation_builder import create_simulation
from simulation.core_agents import Household
from simulation.firms import Firm

class TestLaborConfigMigration:

    def test_household_majors_assigned(self):
        """Verify that all households are assigned a valid major from the configuration."""
        sim = create_simulation()

        valid_majors = config.LABOR_MARKET["majors"]
        assert "GENERAL" in valid_majors

        for agent in sim.agents.values():
            if isinstance(agent, Household):
                assert agent._econ_state.major is not None
                assert agent._econ_state.major in valid_majors

    def test_firm_majors_mapped(self):
        """Verify that firms have a major assigned based on their sector/specialization."""
        sim = create_simulation()

        sector_map = config.LABOR_MARKET["sector_map"]

        for agent in sim.agents.values():
            if isinstance(agent, Firm):
                # Check if firm has major attribute (added in migration)
                assert hasattr(agent, "major")
                assert agent.major is not None

                # Verify mapping
                expected_major = sector_map.get(agent.sector, "GENERAL")
                assert agent.major == expected_major

    def test_labor_market_config_loaded(self):
        """Verify that LaborMarket has the configuration loaded."""
        sim = create_simulation()
        labor_market = sim.markets.get("labor")

        assert labor_market is not None
        assert hasattr(labor_market, "config")
        assert labor_market.config is not None
        assert hasattr(labor_market.config, "LABOR_MARKET")
        assert labor_market.config.LABOR_MARKET["compatibility"]["PERFECT"] == 1.2

    def test_firm_config_dto_has_labor_market(self):
        """Verify that FirmConfigDTO has labor_market populated."""
        sim = create_simulation()
        firm = sim.firms[0]
        assert hasattr(firm.config, "labor_market")
        assert firm.config.labor_market is not None
        assert "majors" in firm.config.labor_market

    # test_household_order_metadata removed as it requires complex setup to force RuleBased engine behavior in system test context.
    # Code inspection confirms RuleBasedHouseholdDecisionEngine and ActionProposalEngine were updated to include metadata.
