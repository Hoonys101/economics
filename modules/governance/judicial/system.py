from typing import Dict, Any, Optional
import logging
from modules.common.config_manager.api import ConfigManager
from modules.events.dtos import FinancialEvent, LoanDefaultedEvent
from modules.system.event_bus.api import IEventBus
from modules.governance.judicial.api import IJudicialSystem
from simulation.finance.api import ISettlementSystem
from modules.system.api import IAgentRegistry
from modules.finance.api import (
    IShareholderRegistry, IPortfolioHandler, ICreditFrozen, IFinancialEntity
)
from modules.simulation.api import IEducated
from modules.system.api import DEFAULT_CURRENCY

logger = logging.getLogger(__name__)

class JudicialSystem(IJudicialSystem):
    def __init__(self,
                 event_bus: IEventBus,
                 settlement_system: ISettlementSystem,
                 agent_registry: IAgentRegistry,
                 shareholder_registry: IShareholderRegistry,
                 config_manager: ConfigManager):
        self.event_bus = event_bus
        self.settlement_system = settlement_system
        self.agent_registry = agent_registry
        self.shareholder_registry = shareholder_registry
        self.config_manager = config_manager

        # Subscribe
        self.event_bus.subscribe("LOAN_DEFAULTED", self.handle_financial_event)

    def handle_financial_event(self, event: FinancialEvent) -> None:
        if event['event_type'] == "LOAN_DEFAULTED":
            loan_event = event # Type narrowing
            self.apply_default_penalty(
                agent_id=loan_event['agent_id'],
                defaulted_amount=loan_event['defaulted_amount'],
                loan_id=loan_event['loan_id'],
                tick=loan_event['tick']
            )

            # Seize assets logic
            self.execute_asset_seizure(
                agent_id=loan_event['agent_id'],
                creditor_id=loan_event['creditor_id'],
                amount=loan_event['defaulted_amount'],
                loan_id=loan_event['loan_id'],
                tick=loan_event['tick']
            )

    def apply_default_penalty(self, agent_id: int, defaulted_amount: float, loan_id: str, tick: int) -> None:
        agent = self.agent_registry.get_agent(agent_id)
        if not agent:
            logger.warning(f"JudicialSystem: Agent {agent_id} not found for penalty application.")
            return

        # 1. Share Seizure
        if isinstance(agent, IPortfolioHandler):
            portfolio = agent.get_portfolio()
            for asset in portfolio.assets:
                if asset.asset_type == 'stock':
                    try:
                        firm_id = int(asset.asset_id)
                        if self.shareholder_registry:
                            self.shareholder_registry.register_shares(firm_id, agent_id, 0)
                    except ValueError:
                        pass
            agent.clear_portfolio()
            logger.info(f"JudicialSystem: Seized portfolio of Agent {agent_id}.")

        # 2. Credit Freeze
        if isinstance(agent, ICreditFrozen):
            default_recovery = self.config_manager.get("finance.bank_defaults.credit_recovery_ticks", 100)
            jail_ticks = self.config_manager.get("bank.credit_recovery_ticks", default_recovery)
            agent.credit_frozen_until_tick = tick + jail_ticks
            logger.info(f"JudicialSystem: Credit frozen for Agent {agent_id} until tick {agent.credit_frozen_until_tick}.")

        # 3. XP Penalty
        if isinstance(agent, IEducated):
            default_penalty = self.config_manager.get("finance.bank_defaults.bankruptcy_xp_penalty", 0.2)
            xp_penalty = self.config_manager.get("bank.bankruptcy_xp_penalty", default_penalty)
            agent.education_xp *= (1.0 - xp_penalty)
            logger.info(f"JudicialSystem: Applied XP penalty to Agent {agent_id}.")

    def execute_asset_seizure(self, agent_id: int, creditor_id: int, amount: float, loan_id: str, tick: int) -> None:
        agent = self.agent_registry.get_agent(agent_id)
        creditor = self.agent_registry.get_agent(creditor_id)

        if not agent or not creditor:
            return

        # Determine seizable amount (all liquid assets)
        seizable_amount = 0.0

        # Accessing `assets` directly to check balance.
        # We prioritize IFinancialEntity interface
        if isinstance(agent, IFinancialEntity):
             seizable_amount = agent.assets
        # Fallback if agent exposes wallet directly
        elif hasattr(agent, 'wallet'):
             seizable_amount = agent.wallet.get_balance(DEFAULT_CURRENCY)

        if seizable_amount <= 0:
            return

        memo = f"Asset Seizure: Default {loan_id}"

        # We assume agents retrieved from registry implement IFinancialEntity
        # as required by ISettlementSystem.

        tx = self.settlement_system.transfer(
            debit_agent=agent, # type: ignore
            credit_agent=creditor, # type: ignore
            amount=seizable_amount,
            memo=memo,
            tick=tick
        )

        if tx:
            logger.info(f"JudicialSystem: Seized {seizable_amount} from Agent {agent_id} for Creditor {creditor_id}.")
