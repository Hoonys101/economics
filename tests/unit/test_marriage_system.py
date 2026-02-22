import pytest
from unittest.mock import MagicMock
from simulation.systems.marriage_system import MarriageSystem
from simulation.dtos.api import SimulationState
from modules.finance.wallet.wallet import Wallet
from modules.household.dtos import BioStateDTO, EconStateDTO

# Dummy Household to behave like the real object for property access
class DummyHousehold:
    def __init__(self, id, age, gender, wealth):
        self.id = id
        self.is_active = True
        self._bio_state = BioStateDTO(
            id=id, age=age, gender=gender, generation=0, is_active=True, needs={}, spouse_id=None,
            sex=gender # Sync sex with gender for test
        )
        wallet = Wallet(owner_id=id)
        wallet.add(wealth)
        self._econ_state = EconStateDTO(
            wallet=wallet, inventory={}, inventory_quality={}, durable_assets=[], portfolio=MagicMock(),
            is_employed=True, employer_id=None, current_wage_pennies=0, wage_modifier=1.0,
            labor_skill=1.0, education_xp=0.0, education_level=0, owned_properties=[],
            residing_property_id=id*100, is_homeless=False, home_quality_score=1.0, housing_target_mode="RENT",
            housing_price_history=None, market_wage_history=None, shadow_reservation_wage_pennies=0,
            last_labor_offer_tick=0, last_fired_tick=-1, job_search_patience=0, employment_start_tick=0,
            current_consumption=0.0, current_food_consumption=0.0, expected_inflation={}, perceived_avg_prices={},
            price_history=None, price_memory_length=10, adaptation_rate=0.1,
            labor_income_this_tick_pennies=0, capital_income_this_tick_pennies=0,
            consumption_expenditure_this_tick_pennies=0, food_expenditure_this_tick_pennies=0
        )

    @property
    def age(self): return self._bio_state.age

    @property
    def gender(self): return self._bio_state.gender

    @property
    def spouse_id(self): return self._bio_state.spouse_id

    @spouse_id.setter
    def spouse_id(self, val): self._bio_state.spouse_id = val

    @property
    def total_wealth(self): return self._econ_state.wallet.get_balance()

    @property
    def balance_pennies(self): return self._econ_state.wallet.get_balance()

    @property
    def residing_property_id(self): return self._econ_state.residing_property_id

    @residing_property_id.setter
    def residing_property_id(self, val): self._econ_state.residing_property_id = val

class TestMarriageSystem:
    @pytest.fixture
    def household_factory(self):
        def _create(id, age, gender, wealth):
            return DummyHousehold(id, age, gender, wealth)
        return _create

    def test_marriage_matching_and_merge(self, household_factory):
        system = MarriageSystem(config=None)

        # Create eligible couple
        h1 = household_factory(id=1, age=25, gender="M", wealth=10000)
        h2 = household_factory(id=2, age=24, gender="F", wealth=5000)

        # Setup Simulation State
        state = MagicMock(spec=SimulationState)
        state.households = [h1, h2]

        # Mock Settlement System
        settlement = MagicMock()
        state.settlement_system = settlement

        # Run Execution
        system.execute(state)

        # Verify Matching happened
        print(f"DEBUG: h1.spouse_id={h1.spouse_id}, h2.spouse_id={h2.spouse_id}")
        assert h1.spouse_id == h2.id
        assert h2.spouse_id == h1.id

        # Verify Wealth Transfer
        # h1 (wealthier) should be HOH
        settlement.transfer.assert_called_with(
            sender_id=h2.id, receiver_id=h1.id, amount=5000, currency="USD", memo="MARRIAGE_MERGE"
        )

        # Verify Wallet Merge
        assert h2._econ_state.wallet is h1._econ_state.wallet

        # Verify Housing Merge
        assert h2.residing_property_id == h1.residing_property_id

    def test_no_match_age_gap(self, household_factory):
        system = MarriageSystem(config=None)

        h1 = household_factory(id=1, age=20, gender="M", wealth=10000)
        h2 = household_factory(id=2, age=30, gender="F", wealth=5000) # 10 years gap

        state = MagicMock(spec=SimulationState)
        state.households = [h1, h2]
        state.settlement_system = MagicMock()

        system.execute(state)

        assert h1.spouse_id is None
        assert h2.spouse_id is None
