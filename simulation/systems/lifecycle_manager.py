from __future__ import annotations
from typing import List, TYPE_CHECKING, Any, Optional
import logging

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState
    from simulation.models import Transaction
    from modules.household.api import IHouseholdFactory
    from modules.hr.api import IHRService
    from modules.finance.api import ITaxService
    from modules.system.api import IAgentRegistry

from simulation.systems.api import AgentLifecycleManagerInterface
from simulation.systems.demographic_manager import DemographicManager
from simulation.systems.immigration_manager import ImmigrationManager
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.systems.firm_management import FirmSystem
from simulation.systems.liquidation_manager import LiquidationManager
from simulation.finance.api import ISettlementSystem
from modules.system.api import IAssetRecoverySystem
from modules.system.registry import AgentRegistry
from modules.hr.service import HRService
from modules.finance.service import TaxService
from modules.finance.api import IShareholderRegistry
from modules.simulation.api import IEstateRegistry

# New Imports
from simulation.systems.lifecycle.api import LifecycleConfigDTO, BirthConfigDTO, DeathConfigDTO
from simulation.systems.lifecycle.aging_system import AgingSystem
from simulation.systems.lifecycle.birth_system import BirthSystem
from simulation.systems.lifecycle.death_system import DeathSystem
from simulation.systems.lifecycle.marriage_system import MarriageSystem
from simulation.ai.vectorized_planner import VectorizedHouseholdPlanner

class AgentLifecycleManager(AgentLifecycleManagerInterface):
    """
    Handles agent creation, aging, death, and liquidation.
    WO-103: Implements SystemInterface.
    WO-109: Returns transactions for deferred execution (Sacred Sequence).
    """

    def __init__(self, config_module: Any, demographic_manager: DemographicManager,
                 inheritance_manager: InheritanceManager, firm_system: FirmSystem,
                 settlement_system: ISettlementSystem, public_manager: IAssetRecoverySystem, logger: logging.Logger,
                 shareholder_registry: IShareholderRegistry = None,
                 household_factory: Optional[IHouseholdFactory] = None,
                 hr_service: Optional[IHRService] = None,
                 tax_service: Optional[ITaxService] = None,
                 agent_registry: Optional[IAgentRegistry] = None,
                 estate_registry: Optional[IEstateRegistry] = None):

        self.config = config_module
        self.logger = logger

        # Dependencies for LiquidationManager
        # Prefer injected dependencies, fallback to instantiation for backward compatibility
        self.agent_registry = agent_registry if agent_registry else AgentRegistry()
        self.hr_service = hr_service if hr_service else HRService()
        self.tax_service = tax_service if tax_service else TaxService(self.agent_registry)

        # TD-187: Liquidation Waterfall
        self.liquidation_manager = LiquidationManager(
            settlement_system,
            self.hr_service,
            self.tax_service,
            self.agent_registry,
            shareholder_registry,
            public_manager
        )

        # Instantiate Sub-Systems
        # DTO Injection for AgingSystem
        lifecycle_config = LifecycleConfigDTO.from_config_module(config_module)
        self.aging_system = AgingSystem(lifecycle_config, demographic_manager, logger)

        if household_factory is None:
             raise ValueError("IHouseholdFactory is mandatory for AgentLifecycleManager.")

        # Create DTOs and dependencies
        birth_config = BirthConfigDTO.from_config_module(config_module)
        death_config = DeathConfigDTO.from_config_module(config_module)
        breeding_planner = VectorizedHouseholdPlanner(config_module)

        self.birth_system = BirthSystem(
            birth_config,
            breeding_planner,
            demographic_manager,
            ImmigrationManager(config_module=config_module, settlement_system=settlement_system),
            firm_system,
            settlement_system,
            logger,
            household_factory
        )

        self.death_system = DeathSystem(
            death_config,
            inheritance_manager,
            self.liquidation_manager,
            settlement_system,
            public_manager,
            logger,
            estate_registry=estate_registry
        )

        self.marriage_system = MarriageSystem(settlement_system, logger)

    def reset_agents_tick_state(self, state: SimulationState) -> None:
        """
        Calls the reset method on all active agents at the end of a tick.
        """
        self.logger.debug("LIFECYCLE_PULSE | Resetting tick-level state for all agents.")
        for household in state.households:
            if household.is_active:
                household.reset_tick_state()

        for firm in state.firms:
            if firm.is_active:
                firm.reset()

    def execute(self, state: SimulationState) -> List[Transaction]:
        """
        Processes lifecycle events for the tick.
        Returns:
            List[Transaction]: Transactions generated by lifecycle events (e.g., inheritance)
                                to be queued for the NEXT tick.
        """
        # Update AgentRegistry with current state
        # Note: Ideally this should be done by the orchestrator, but keeping it here for safety.
        # But AgentRegistry is used by LiquidationManager via DeathSystem.
        self.agent_registry.set_state(state)

        all_transactions = []

        # 1. Aging Phase
        # AgingSystem is side-effect heavy (aging, distress), currently returns no transactions.
        aging_txs = self.aging_system.execute(state)
        all_transactions.extend(aging_txs)

        # 2. Birth Phase
        # BirthSystem now returns transactions for birth gifts.
        birth_txs = self.birth_system.execute(state)
        all_transactions.extend(birth_txs)

        # 3. Marriage Phase (Wave 4)
        # Execute before Death to ensure spouses are linked if one dies.
        marriage_txs = self.marriage_system.execute(state)
        all_transactions.extend(marriage_txs)

        # 4. Death Phase
        # DeathSystem returns transactions (inheritance, liquidation leftovers)
        death_txs = self.death_system.execute(state)
        all_transactions.extend(death_txs)

        return all_transactions

if __name__ == "__main__":
    pass
