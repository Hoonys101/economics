import pytest
from unittest.mock import MagicMock
from simulation.agents.government import Government
from simulation.policies.adaptive_gov_policy import AdaptiveGovPolicy
from simulation.dtos import GovernmentStateDTO
from simulation.ai.enums import PolicyActionTag, PoliticalParty, Personality
from modules.household.political_component import PoliticalComponent
from modules.household.dtos import SocialStateDTO

class TestLeviathanEmergence:

    def test_scapegoat_emergence(self):
        """
        WO-4.6: Scapegoat Test
        - Force approval < 20%
        - Assert fire_advisor is eventually called (via policy decision)
        - Assert subsequent action tags are locked
        """
        # 1. Setup
        config = MagicMock()
        config.GOV_ACTION_INTERVAL = 1 # Force action every tick
        config.TICKS_PER_YEAR = 360 # Default

        gov = Government(id=1, initial_assets=1000.0, config_module=config)
        policy = AdaptiveGovPolicy(gov, config)

        # 2. Force Low Approval
        sensory_data = GovernmentStateDTO(
            tick=10,
            inflation_sma=0.02,
            unemployment_sma=0.05,
            gdp_growth_sma=0.01,
            wage_sma=10.0,
            approval_sma=0.1, # Critical!
            current_gdp=1000.0,
            gini_index=0.3,
            approval_low_asset=0.1,
            approval_high_asset=0.1
        )

        # 3. Execute Decision
        # Ensure lockout manager is fresh
        gov.policy_lockout_manager.policy_locks = {}

        decision = policy.decide(gov, sensory_data, 10, MagicMock())

        # 4. Assertions
        assert decision["status"] == "EXECUTED"
        assert decision["action_taken"] == "Fire Advisor (Scapegoat)"

        # Verify Lockout
        # We know implementation fires KEYNESIAN advisor -> locks KEYNESIAN_FISCAL
        is_locked = gov.policy_lockout_manager.is_locked(PolicyActionTag.KEYNESIAN_FISCAL, 10)
        assert is_locked is True

    def test_paradox_support_emergence(self):
        """
        WO-4.6: Paradox Support Test
        - Create poor households with Personality.GROWTH_ORIENTED
        - Assert high approval for BLUE party despite negative income growth (implied by poor status)
        """
        # 1. Setup
        political_component = PoliticalComponent()

        # Growth Oriented Personality
        personality = Personality.GROWTH_ORIENTED

        # Initialize State
        economic_vision, trust_score = political_component.initialize_state(personality)

        state = SocialStateDTO(
            personality=personality,
            social_status=0.0,
            discontent=0.0,
            approval_rating=0, # Initially 0
            conformity=0.5,
            social_rank=0.1, # Low rank
            quality_preference=0.5,
            brand_loyalty={},
            last_purchase_memory={},
            patience=0.5,
            optimism=0.9,
            ambition=0.9,
            last_leisure_type="IDLE",
            demand_elasticity=1.0,
            economic_vision=economic_vision,
            trust_score=trust_score,
            desire_weights={}
        )

        # 2. Simulate Poor Status (High Survival Need)
        survival_need = 80.0 # High need = Poor

        # 3. Update Opinion for BLUE Party (Growth)
        updated_state = political_component.update_opinion(
            state,
            survival_need,
            PoliticalParty.BLUE
        )

        # 4. Assertions
        # Expectation: Even though survival need is high (satisfaction low),
        # the ideological match with BLUE (Growth) should override it for GROWTH_ORIENTED personality.

        # Calculation check:
        # Gov Stance = 0.9 (Blue)
        # Vision = ~0.9
        # Match = 1.0
        # Discontent = 0.8 -> Satisfaction = 0.2
        # Approval Score = 0.4*0.2 + 0.6*1.0 = 0.08 + 0.6 = 0.68 > 0.5

        assert updated_state.approval_rating == 1
        assert updated_state.economic_vision > 0.7 # Verify vision is high

    def test_political_business_cycle_emergence(self):
        """
        WO-4.6: Political Business Cycle Test
        - Assert spending increases (or taxes cut) near election (tick % 100 >= 80).
        """
        config = MagicMock()
        config.GOV_ACTION_INTERVAL = 1
        config.TICKS_PER_YEAR = 360
        config.INCOME_TAX_RATE = 0.1
        config.CORPORATE_TAX_RATE = 0.2
        config.TICKS_PER_YEAR = 360

        gov = Government(id=1, initial_assets=1000.0, config_module=config)
        policy = AdaptiveGovPolicy(gov, config)

        # Setup BLUE party (Growth/HighAsset focus)
        gov.ruling_party = PoliticalParty.BLUE

        # Case 1: Near Election (Tick 90)
        sensory_data_election = GovernmentStateDTO(
            tick=90,
            inflation_sma=0.02,
            unemployment_sma=0.05,
            gdp_growth_sma=0.01,
            wage_sma=10.0,
            approval_sma=0.5,
            current_gdp=1000.0,
            gini_index=0.3,
            approval_low_asset=0.5,
            approval_high_asset=0.5
        )

        decision_election = policy.decide(gov, sensory_data_election, 90, MagicMock())

        # Expectation: Tax Cut (Stimulus for Blue) or Fiscal Stimulus
        # Blue likes Tax Cut (Corp) -> +HighAssetApproval
        # With new weights (0.9 Approval), this should be highly prioritized.
        assert decision_election["status"] == "EXECUTED"
        assert decision_election["action_taken"] in ["Tax Cut (Corp)", "Fiscal Stimulus (Welfare+)", "Tax Cut (Income)"]
