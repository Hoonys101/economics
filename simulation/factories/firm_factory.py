from __future__ import annotations
from typing import Optional, Dict, Any, TYPE_CHECKING
import logging
import copy
from dataclasses import replace

from simulation.firms import Firm
from modules.simulation.dtos.api import FirmConfigDTO
from modules.simulation.api import AgentCoreConfigDTO, AgentStateDTO
from modules.system.api import DEFAULT_CURRENCY
from simulation.ai.enums import Personality
from modules.finance.api import ISettlementSystem, ICentralBank
from modules.system.constants import ID_BANK
from simulation.systems.bootstrapper import Bootstrapper

if TYPE_CHECKING:
    from simulation.loan_market import LoanMarket

logger = logging.getLogger(__name__)

class FirmFactory:
    """
    Factory for creating Firm agents.
    Encapsulates creation logic and cloning.
    """

    def __init__(self, config_module: Any):
        self.config_module = config_module

    def create_firm(
        self,
        agent_id: int,
        name: str,
        config_dto: FirmConfigDTO,
        specialization: str,
        productivity_factor: float,
        settlement_system: ISettlementSystem,
        central_bank: ICentralBank,
        sector: str = "FOOD",
        personality: Optional[Personality] = None,
        initial_inventory: Optional[Dict[str, float]] = None,
        loan_market: Optional[LoanMarket] = None,
        decision_engine: Optional[Any] = None,
        simulation: Optional[Any] = None # For logger/memory access if needed
    ) -> Firm:
        """
        Creates a new Firm agent.
        """
        # Core Config
        core_config = AgentCoreConfigDTO(
            id=agent_id,
            name=name,
            value_orientation="Growth", # Firms usually default to Growth?
            initial_needs={}, # Firms don't have bio needs
            logger=logger if not simulation else simulation.logger,
            memory_interface=None if not simulation else getattr(simulation, "persistence_manager", None)
        )

        firm = Firm(
            core_config=core_config,
            engine=decision_engine, # Must be provided or created externally for now
            specialization=specialization,
            productivity_factor=productivity_factor,
            config_dto=config_dto,
            initial_inventory=initial_inventory,
            loan_market=loan_market,
            sector=sector,
            personality=personality
        )

        # Inject Settlement System dependency
        firm.settlement_system = settlement_system

        # Atomic Initialization: Register Account & Inject Liquidity
        if settlement_system:
            # 1. Register Account
            settlement_system.register_account(ID_BANK, firm.id)

            # 2. Inject Initial Liquidity (if Central Bank provided)
            # This ensures the firm starts with the minimum required capital/inventory
            if central_bank:
                # Bootstrapper expects the full config module (with GOODS constant), not the DTO
                Bootstrapper.inject_liquidity_for_firm(firm, self.config_module, settlement_system, central_bank)

        return firm

    def clone_firm(self, source_firm: Firm, new_id: int, initial_assets_from_parent: int, current_tick: int) -> Firm:
        """
        Deep copy / Mitosis logic for Firms.
        Replaces Firm.clone().
        """
        cloned_decision_engine = copy.deepcopy(source_firm.decision_engine)

        # Create new Core Config based on source but with new ID
        new_core_config = replace(source_firm.get_core_config(), id=new_id, name=f"Firm_{new_id}")

        new_firm = Firm(
            core_config=new_core_config,
            engine=cloned_decision_engine,
            specialization=source_firm.specialization,
            productivity_factor=source_firm.productivity_factor,
            config_dto=source_firm.config,
            initial_inventory=source_firm.get_all_items(),
            loan_market=source_firm.decision_engine.loan_market,
            personality=source_firm.personality
        )

        # Hydrate State
        # Note: We manually hydrate to ensure clean state
        initial_state = AgentStateDTO(
            assets={DEFAULT_CURRENCY: initial_assets_from_parent},
            inventory=copy.deepcopy(source_firm._inventory),
            is_active=True
        )
        new_firm.load_state(initial_state)

        # Handle internal inventories not covered by AgentStateDTO legacy load
        new_firm._input_inventory = copy.deepcopy(source_firm._input_inventory)
        new_firm._input_inventory_quality = copy.deepcopy(source_firm._input_inventory_quality)

        # Preserve quality for main inventory (Fixing potential bug in legacy clone)
        new_firm.inventory_quality = copy.deepcopy(source_firm.inventory_quality)

        # Transfer Settlement System dependency
        if hasattr(source_firm, 'settlement_system'):
            new_firm.settlement_system = source_firm.settlement_system
            # Register Bank Account for the new firm
            if new_firm.settlement_system:
                new_firm.settlement_system.register_account(ID_BANK, new_firm.id)

        new_firm.logger.info(
            f"Firm {source_firm.id} was cloned to new Firm {new_id}",
            extra={
                "original_agent_id": source_firm.id,
                "new_agent_id": new_id,
                "tags": ["lifecycle", "clone"],
            },
        )
        return new_firm
