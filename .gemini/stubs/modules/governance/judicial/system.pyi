from _typeshed import Incomplete
from modules.common.config_manager.api import ConfigManager as ConfigManager
from modules.events.dtos import FinancialEvent as FinancialEvent
from modules.finance.api import ICreditFrozen as ICreditFrozen, IFinancialAgent as IFinancialAgent, ILiquidatable as ILiquidatable, IPortfolioHandler as IPortfolioHandler, IShareholderRegistry as IShareholderRegistry
from modules.governance.judicial.api import DebtRestructuringRequiredEvent as DebtRestructuringRequiredEvent, IJudicialSystem as IJudicialSystem, LoanDefaultedEvent as LoanDefaultedEvent, SeizureResultDTO as SeizureResultDTO
from modules.simulation.api import IEducated as IEducated
from modules.system.api import AgentID as AgentID, DEFAULT_CURRENCY as DEFAULT_CURRENCY, IAgentRegistry as IAgentRegistry
from modules.system.event_bus.api import IEventBus as IEventBus
from simulation.finance.api import ISettlementSystem as ISettlementSystem

logger: Incomplete

class JudicialSystem(IJudicialSystem):
    event_bus: Incomplete
    settlement_system: Incomplete
    agent_registry: Incomplete
    shareholder_registry: Incomplete
    config_manager: Incomplete
    def __init__(self, event_bus: IEventBus, settlement_system: ISettlementSystem, agent_registry: IAgentRegistry, shareholder_registry: IShareholderRegistry, config_manager: ConfigManager) -> None: ...
    def handle_financial_event(self, event: FinancialEvent) -> None: ...
    def apply_default_penalty(self, agent_id: AgentID, tick: int) -> None: ...
    def assess_solvency(self, agent_id: AgentID) -> bool:
        """
        Check if an agent is solvent based on SSoT balances.
        For now, simply checks if balance is non-negative.
        """
    def handle_default(self, event: LoanDefaultedEvent) -> SeizureResultDTO: ...
