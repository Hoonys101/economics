from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from simulation.models import Transaction

if TYPE_CHECKING:
    from simulation.agents.government import Government
    from simulation.systems.settlement_system import SettlementSystem
    from modules.government.taxation.system import TaxationSystem
    from modules.finance.api import IShareholderRegistry
    from logging import Logger

# Alias for Spec Compliance
TransactionDTO = Transaction

@dataclass
class TransactionResult:
    """Result of a transaction processing attempt."""
    success: bool
    transaction_id: Optional[str] = None
    error_message: Optional[str] = None
    amount_processed: int = 0 # Changed to int (pennies)

@dataclass(frozen=True)
class TransactionContext:
    """
    Provides all necessary simulation state to a transaction handler.
    This is an immutable snapshot of state for a single transaction,
    ensuring that handlers have a consistent view of the world.
    Moved from simulation/systems/api.py for DTO Purity.
    """
    agents: Dict[int, Any]
    inactive_agents: Dict[int, Any]
    government: 'Government'
    settlement_system: 'SettlementSystem'
    taxation_system: 'TaxationSystem'
    stock_market: Any
    real_estate_units: List[Any]
    market_data: Dict[str, Any]
    config_module: Any
    logger: 'Logger'
    time: int
    bank: Optional[Any] # Bank
    central_bank: Optional[Any] # CentralBank
    public_manager: Optional[Any] # PublicManager
    transaction_queue: List['Transaction'] # For appending side-effect transactions (e.g. credit creation)
    shareholder_registry: Optional['IShareholderRegistry'] = None # TD-275
    estate_registry: Optional[Any] = None
