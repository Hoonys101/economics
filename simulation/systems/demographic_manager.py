
from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging
import random
from simulation.core_agents import Household
from simulation.utils.config_factory import create_config_dto
from modules.system.api import DEFAULT_CURRENCY
from modules.household.api import IHouseholdFactory, HouseholdFactoryContext
from simulation.factories.household_factory import HouseholdFactory
from modules.demographics.api import IDemographicManager, DemographicStatsDTO, GenderStatsDTO

if TYPE_CHECKING:
    from simulation.dtos.strategy import ScenarioStrategy
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class DemographicManager(IDemographicManager):
    """
    Optimized Demographic Manager (Phase 17)
    - O(1) Statistical Retrieval via event-driven caching.
    - Single Source of Truth for agent lifecycle (birth/death).
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DemographicManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_module: Any = None, strategy: Optional["ScenarioStrategy"] = None, household_factory: Optional[IHouseholdFactory] = None):
        if hasattr(self, "initialized") and self.initialized:
            return

        self.config_module = config_module
        self.strategy = strategy
        self.logger = logging.getLogger("simulation.systems.demographic_manager")
        self.settlement_system: Optional[Any] = None 
        self.household_factory = household_factory
        
        # O(1) Stats Cache
        self._stats_cache = {
            "M": {"count": 0, "total_labor_hours": 0.0},
            "F": {"count": 0, "total_labor_hours": 0.0}
        }

        self.initialized = True
        self.logger.info("DemographicManager initialized with O(1) cache.")

    def set_world_state(self, world_state: "WorldState") -> None:
        self.world_state = world_state

    def get_gender_stats(self) -> DemographicStatsDTO:
        """
        Retrieves demographic statistics in O(1).
        """
        m_stats = self._stats_cache["M"]
        f_stats = self._stats_cache["F"]
        
        m_count = m_stats["count"]
        f_count = f_stats["count"]
        
        res: DemographicStatsDTO = {
            "M": {
                "count": m_count,
                "total_labor_hours": m_stats["total_labor_hours"],
                "avg_labor_hours": m_stats["total_labor_hours"] / m_count if m_count > 0 else 0.0
            },
            "F": {
                "count": f_count,
                "total_labor_hours": f_stats["total_labor_hours"],
                "avg_labor_hours": f_stats["total_labor_hours"] / f_count if f_count > 0 else 0.0
            },
            "total_population": m_count + f_count,
            "active_population": m_count + f_count  # Simplifying active to mean alive
        }
        return res

    def register_birth(self, agent: Any) -> None:
        """Registers birth and updates cache."""
        gender = getattr(agent, "gender", None)
        if gender in self._stats_cache:
            self._stats_cache[gender]["count"] += 1
            self.logger.debug(f"Cache update (birth): {gender} count ++ -> {self._stats_cache[gender]['count']}")

    def register_death(self, agent: Any, cause: str = "NATURAL") -> None:
        """Single Source of Truth for lifecycle termination."""
        if not getattr(agent, "is_active", False):
            return

        agent.is_active = False
        gender = getattr(agent, "gender", None)
        if gender in self._stats_cache:
            self._stats_cache[gender]["count"] = max(0, self._stats_cache[gender]["count"] - 1)
            self.logger.debug(f"Cache update (death): {gender} count -- -> {self._stats_cache[gender]['count']}")
        
        self.logger.info(f"LIFE_END | Agent {getattr(agent, 'id', 'unknown')} terminated. Cause: {cause}")

    def update_labor_hours(self, gender: str, delta: float) -> None:
        """Updates labor hour running totals (called by agents on time allocation change)."""
        if gender in self._stats_cache:
            self._stats_cache[gender]["total_labor_hours"] += delta

    def sync_stats(self, agents: List[Any]) -> None:
        """Rebuilds cache from active agent list (O(N) recovery)."""
        self._stats_cache = {
            "M": {"count": 0, "total_labor_hours": 0.0},
            "F": {"count": 0, "total_labor_hours": 0.0}
        }
        for agent in agents:
            if getattr(agent, "is_active", False):
                gender = getattr(agent, "gender", None)
                if gender in self._stats_cache:
                    self._stats_cache[gender]["count"] += 1
                    # Note: We can only sync labor if we calculate it now (O(N)) or if agents track it.
                    # For sync, we might need a full recalc if called mid-simulation.
        self.logger.info(f"Stats cache synchronized. Total M: {self._stats_cache['M']['count']}, Total F: {self._stats_cache['F']['count']}")

    def process_aging(self, agents: List[Household], current_tick: int, market_data: Optional[Dict[str, Any]] = None) -> None:
        # MIGRATION: Logic migrated to LifecycleEngine/Household.update_needs
        # DemographicManager no longer drives aging logic directly, it delegates to agent update.
        for agent in agents:
            if not agent.is_active:
                continue

            # This call triggers LifecycleEngine -> death check -> register_death
            agent.update_needs(current_tick, market_data)

    def process_births(self, simulation: Any, birth_requests: List[Household]) -> List[Household]:
        new_children = []

        for parent in birth_requests:
            if not (self.config_module.REPRODUCTION_AGE_START <= parent.age <= self.config_module.REPRODUCTION_AGE_END):
                continue

            child_id = simulation.next_agent_id
            simulation.next_agent_id += 1

            parent_assets = 0
            if hasattr(parent, 'wallet'):
                parent_assets = parent.wallet.get_balance(DEFAULT_CURRENCY)
            elif hasattr(parent, 'assets'):
                 parent_assets = int(parent.assets)

            initial_gift_pennies = int(max(0, min(parent_assets * 0.1, parent_assets)))

            try:
                if not self.household_factory:
                    config_module = getattr(simulation, 'config', self.config_module)
                    context = HouseholdFactoryContext(
                        core_config_module=config_module,
                        household_config_dto=create_config_dto(config_module),
                        goods_data=getattr(simulation, 'goods_data', []),
                        loan_market=getattr(simulation, 'loan_market', None),
                        ai_training_manager=getattr(simulation, 'ai_trainer', None),
                        settlement_system=getattr(simulation, 'settlement_system', None),
                        markets=getattr(simulation, 'markets', {}),
                        memory_system=getattr(simulation, 'memory_system', None),
                        central_bank=getattr(simulation, 'central_bank', None),
                        demographic_manager=self
                    )
                    self.household_factory = HouseholdFactory(context)

                child = self.household_factory.create_newborn(parent, simulation, child_id)
                
                # Update parent linkage
                parent.children_ids.append(child_id)
                
                # Register Birth in system (O(1) update)
                self.register_birth(child)
                
                new_children.append(child)

                if initial_gift_pennies > 0:
                    settlement = self.settlement_system or getattr(simulation, "settlement_system", None)
                    if settlement:
                         settlement.transfer(parent, child, initial_gift_pennies, "BIRTH_GIFT")
                    else:
                         self.logger.error("BIRTH_ERROR | SettlementSystem not found.")

                self.logger.info(f"BIRTH | Parent {parent.id} -> Child {child.id}")
            except Exception as e:
                self.logger.error(f"BIRTH_FAILED | {e}")
                continue

        return new_children
