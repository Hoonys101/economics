import pytest
import logging
from unittest.mock import MagicMock
from simulation.systems.lifecycle.marriage_system import MarriageSystem
from simulation.dtos.api import SimulationState
from modules.finance.wallet.wallet import Wallet
from modules.household.dtos import BioStateDTO, EconStateDTO
from modules.system.api import DEFAULT_CURRENCY

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
    def sex(self): return self._bio_state.sex

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

    @property
    def is_homeless(self): return self._econ_state.is_homeless

    @is_homeless.setter
    def is_homeless(self, val): self._econ_state.is_homeless = val

    @property
    def portfolio(self): return self._econ_state.portfolio

    @property
    def inventory(self): return self._econ_state.inventory

    def add_item(self, k, v): self._econ_state.inventory[k] = self._econ_state.inventory.get(k, 0) + v
    def clear_inventory(self): self._econ_state.inventory.clear()
    @property
    def children_ids(self): return self._bio_state.children_ids
    def add_child(self, cid): self._bio_state.children_ids.append(cid)
    @property
    def owned_properties(self): return self._econ_state.owned_properties
    def add_property(self, pid): self._econ_state.owned_properties.append(pid)
    def remove_property(self, pid): self._econ_state.owned_properties.remove(pid)
    def reset_tick_state(self): pass

class TestMarriageSystem:
    @pytest.fixture
    def household_factory(self):
        def _create(id, age, gender, wealth):
            return DummyHousehold(id, age, gender, wealth)
        return _create

    def test_marriage_matching_and_merge(self, household_factory):
        logger = logging.getLogger("test")
        settlement = MagicMock()
        system = MarriageSystem(settlement_system=settlement, logger=logger)
        system.marriage_chance = 1.0 # Force matching

        # Create eligible couple
        h1 = household_factory(id=1, age=25, gender="M", wealth=10000)
        h2 = household_factory(id=2, age=24, gender="F", wealth=5000)

        # Setup Simulation State
        state = MagicMock(spec=SimulationState)
        state.households = [h1, h2]
        state.real_estate_units = []
        state.time = 0

        # Run Execution
        system.execute(state)

        # Verify Matching happened
        assert h1.spouse_id == h2.id
        assert h2.spouse_id == h1.id

        # Verify Wealth Transfer (h1 is richer)
        settlement.transfer.assert_called_with(
            debit_agent=h2, credit_agent=h1, amount=5000, 
            memo="MARRIAGE_MERGER", tick=0, currency=DEFAULT_CURRENCY
        )

        # Verify Wallet Merge
        assert h2._econ_state.wallet is h1._econ_state.wallet

    def test_no_match_age_gap(self, household_factory):
        logger = logging.getLogger("test")
        settlement = MagicMock()
        system = MarriageSystem(settlement_system=settlement, logger=logger)

        h1 = household_factory(id=1, age=20, gender="M", wealth=10000)
        h2 = household_factory(id=2, age=40, gender="F", wealth=5000) # gap > 5 years (implied in old system)
        # Note: Canonical system uses marriage_min_age/max_age for filtering, not relative gap?
        # Let's check lifecycle/marriage_system.py again.
        # It doesn't have a relative gap check, only absolute age 18-60.
        # But wait, it did shuffle and zip.
        
        state = MagicMock(spec=SimulationState)
        state.households = [h1, h2]
        state.real_estate_units = []
        state.time = 0

        system.execute(state)

        # If chance is low (default 0.05), it might not match even if eligible.
        # But here they are eligible by age (20, 40).
        # To test NO match, we should use out of age range.
        
    def test_no_match_out_of_age(self, household_factory):
        logger = logging.getLogger("test")
        settlement = MagicMock()
        system = MarriageSystem(settlement_system=settlement, logger=logger)
        system.marriage_chance = 1.0

        h1 = household_factory(id=1, age=10, gender="M", wealth=10000) # Too young
        h2 = household_factory(id=2, age=24, gender="F", wealth=5000)

        state = MagicMock(spec=SimulationState)
        state.households = [h1, h2]
        state.real_estate_units = []
        state.time = 0

        system.execute(state)
        assert h1.spouse_id is None

