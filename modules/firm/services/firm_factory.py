from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Optional, Dict, Any, Type

from modules.simulation.api import AgentCoreConfigDTO, IAgent
from modules.simulation.dtos.api import FirmConfigDTO
from modules.system.api import AgentID

if TYPE_CHECKING:
    from simulation.engine import Simulation
    from simulation.firms import Firm
    from simulation.systems.settlement_system import SettlementSystem

logger = logging.getLogger(__name__)

class FirmFactory:
    """
    Handles atomic creation, registration, and initialization of Firms.
    Fixes TD-LIFECYCLE-GHOST-FIRM.
    """

    @staticmethod
    def create_and_register_firm(
        simulation: "Simulation",
        instance_class: Type["Firm"],
        core_config: AgentCoreConfigDTO,
        firm_config_dto: FirmConfigDTO,
        **kwargs
    ) -> Optional["Firm"]:
        """
        Executes the Atomic Startup Sequence:
        1. Instantiate Firm.
        2. Register in Simulation.
        3. Open Bank Account (implicit via registration in Settlement indices).
        4. Transfer initial funds if provided in kwargs['initial_capital'].
        """
        try:
            # Extract Factory-specific kwargs that shouldn't go to Firm constructor
            founder = kwargs.pop("founder", None)
            startup_cost = kwargs.pop("startup_cost", None)

            # 1. Instantiate
            new_firm = instance_class(
                core_config=core_config,
                config_dto=firm_config_dto,
                **kwargs
            )
            
            # Inject SettlementSystem early
            if hasattr(simulation, "settlement_system"):
                new_firm.settlement_system = simulation.settlement_system

            # 2. Registration (CRITICAL: Must happen before Transfer)
            # Add to main registries so SettlementSystem can find it
            simulation.agents[new_firm.id] = new_firm
            # Use getattr for safety with Mocks
            if hasattr(simulation, "firms") and getattr(instance_class, "__name__", "") == "Firm":
                 simulation.firms.append(new_firm)
            
            if hasattr(simulation, "ai_training_manager"):
                 simulation.ai_training_manager.agents.append(new_firm)

            # 3. Bank Account Opening
            # In this simulation, registering in agents/registry is often enough,
            # but we explicitly register the account if a bank is available.
            if simulation.bank and simulation.settlement_system:
                simulation.settlement_system.register_account(simulation.bank.id, new_firm.id)

            # 4. Initial Capital Injection (if requested)
            if founder and startup_cost:
                success = simulation.settlement_system.transfer(
                    debit_agent=founder,
                    credit_agent=new_firm,
                    amount=int(startup_cost),
                    memo=f"Startup Capital for Firm {new_firm.id}",
                    tick=simulation.time
                )
                if not success:
                    logger.error(f"STARTUP_FAIL | Failed to inject capital into Firm {new_firm.id}. Rolling back registration.")
                    # Rollback
                    del simulation.agents[new_firm.id]
                    if new_firm in simulation.firms: simulation.firms.remove(new_firm)
                    return None

            # 5. Finalize
            if simulation.stock_market:
                new_firm.init_ipo(simulation.stock_market)

            logger.info(f"STARTUP_SUCCESS | Firm {new_firm.id} atomically initialized and registered.")
            return new_firm

        except Exception as e:
            logger.exception(f"STARTUP_FATAL | Unexpected error during firm creation: {e}")
            return None
