from __future__ import annotations
from typing import List, Dict, Optional, TYPE_CHECKING, override

from modules.system.api import DEFAULT_CURRENCY, CurrencyCode
from simulation.models import Skill, Talent
from simulation.portfolio import Portfolio
from simulation.ai.api import Personality

if TYPE_CHECKING:
    from modules.household.dtos import BioStateDTO, EconStateDTO, SocialStateDTO

class HouseholdPropertiesMixin:
    """
    Mixin for Household properties (Getters/Setters).
    Manages access to internal DTO states (Bio, Econ).
    """

    # Type hints for properties expected on self
    _econ_state: "EconStateDTO"
    _bio_state: "BioStateDTO"
    _social_state: "SocialStateDTO"
    _assets: Dict[CurrencyCode, float] # BaseAgent attribute

    @property
    @override
    def assets(self) -> Dict[CurrencyCode, float]:
        return self._econ_state.assets

    @assets.setter
    def assets(self, value: Dict[CurrencyCode, float]) -> None:
        self._econ_state.assets = value
        self._assets = value

    @property
    def _inventory(self) -> Dict[str, float]:
        """
        [Refactor] Internal inventory access via EconStateDTO.
        Overrides BaseAgent._inventory to link with DTO.
        """
        return self._econ_state.inventory

    @_inventory.setter
    def _inventory(self, value: Dict[str, float]) -> None:
        self._econ_state.inventory = value

    @property
    @override
    def inventory(self) -> Dict[str, float]:
        """[DEPRECATED] Use IInventoryHandler methods or self._inventory."""
        return self._econ_state.inventory

    @inventory.setter
    def inventory(self, value: Dict[str, float]) -> None:
        self._econ_state.inventory = value

    @property
    def inventory_quality(self) -> Dict[str, float]:
        return self._econ_state.inventory_quality

    @inventory_quality.setter
    def inventory_quality(self, value: Dict[str, float]) -> None:
        self._econ_state.inventory_quality = value

    @property
    @override
    def needs(self) -> Dict[str, float]:
        return self._bio_state.needs

    @needs.setter
    def needs(self, value: Dict[str, float]) -> None:
        self._bio_state.needs = value

    @property
    def is_active(self) -> bool:
        return self._bio_state.is_active

    @is_active.setter
    def is_active(self, value: bool) -> None:
        self._bio_state.is_active = value

    @property
    def age(self) -> float:
        return self._bio_state.age

    @age.setter
    def age(self, value: float) -> None:
        self._bio_state.age = value

    @property
    def children_ids(self) -> List[int]:
        return self._bio_state.children_ids

    @children_ids.setter
    def children_ids(self, value: List[int]) -> None:
        self._bio_state.children_ids = value

    @property
    def is_homeless(self) -> bool:
        return self._econ_state.is_homeless

    @is_homeless.setter
    def is_homeless(self, value: bool) -> None:
        self._econ_state.is_homeless = value

    @property
    def residing_property_id(self) -> Optional[int]:
        return self._econ_state.residing_property_id

    @residing_property_id.setter
    def residing_property_id(self, value: Optional[int]) -> None:
        self._econ_state.residing_property_id = value

    @property
    def owned_properties(self) -> List[int]:
        return self._econ_state.owned_properties

    @owned_properties.setter
    def owned_properties(self, value: List[int]) -> None:
        self._econ_state.owned_properties = value

    @property
    def current_wage(self) -> float:
        return self._econ_state.current_wage

    @current_wage.setter
    def current_wage(self, value: float) -> None:
        self._econ_state.current_wage = value

    @property
    def is_employed(self) -> bool:
        return self._econ_state.is_employed

    @is_employed.setter
    def is_employed(self, value: bool) -> None:
        self._econ_state.is_employed = value

    @property
    def employer_id(self) -> Optional[int]:
        return self._econ_state.employer_id

    @employer_id.setter
    def employer_id(self, value: Optional[int]) -> None:
        self._econ_state.employer_id = value

    @property
    def skills(self) -> Dict[str, Skill]:
        """[TD-162] Backward compat: Exposes _econ_state.skills."""
        return self._econ_state.skills

    @skills.setter
    def skills(self, value: Dict[str, Skill]) -> None:
        self._econ_state.skills = value

    @property
    def portfolio(self) -> Portfolio:
        """[TD-162] Backward compat: Exposes _econ_state.portfolio."""
        return self._econ_state.portfolio

    @portfolio.setter
    def portfolio(self, value: Portfolio) -> None:
        self._econ_state.portfolio = value

    @property
    def gender(self) -> str:
        """Exposes gender from bio_state."""
        return self._bio_state.gender

    @property
    def home_quality_score(self) -> float:
        """Exposes home_quality_score from econ_state."""
        return self._econ_state.home_quality_score

    @property
    def talent(self) -> Talent:
        """Exposes talent from econ_state."""
        return self._econ_state.talent

    @property
    def demographics(self) -> BioStateDTO:
        """[Legacy] Exposes bio_state as demographics."""
        return self._bio_state

    @property
    def personality(self) -> Personality:
        """Exposes personality from social_state."""
        return self._social_state.personality

    # --- IEmployeeDataProvider Support Properties ---

    @property
    def labor_skill(self) -> float:
        """Exposes labor_skill from econ_state."""
        return self._econ_state.labor_skill

    @labor_skill.setter
    def labor_skill(self, value: float) -> None:
        self._econ_state.labor_skill = value

    @property
    def education_level(self) -> int:
        """Exposes education_level from econ_state."""
        return self._econ_state.education_level

    @education_level.setter
    def education_level(self, value: int) -> None:
        self._econ_state.education_level = value

    @property
    def labor_income_this_tick(self) -> float:
        """Exposes labor_income_this_tick from econ_state."""
        return self._econ_state.labor_income_this_tick

    @labor_income_this_tick.setter
    def labor_income_this_tick(self, value: float) -> None:
        self._econ_state.labor_income_this_tick = value

    @property
    def employment_start_tick(self) -> int:
        """Exposes employment_start_tick from econ_state."""
        return self._econ_state.employment_start_tick

    @employment_start_tick.setter
    def employment_start_tick(self, value: int) -> None:
        self._econ_state.employment_start_tick = value
