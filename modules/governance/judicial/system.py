from typing import Dict, Any, Optional, cast
import logging
from modules.common.config_manager.api import ConfigManager
from modules.events.dtos import FinancialEvent
from modules.system.event_bus.api import IEventBus
from modules.governance.judicial.api import (
    IJudicialSystem, SeizureResultDTO, LoanDefaultedEvent, DebtRestructuringRequiredEvent
)
from simulation.finance.api import ISettlementSystem
from modules.system.api import IAgentRegistry, AgentID
from modules.finance.api import (
    IShareholderRegistry, IPortfolioHandler, ICreditFrozen, IFinancialAgent, ILiquidatable
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
            # Adapt generic FinancialEvent to LoanDefaultedEvent
            loan_event = cast(LoanDefaultedEvent, event)

            self.apply_default_penalty(
                agent_id=loan_event['agent_id'],
                tick=loan_event['tick']
            )

            self.handle_default(loan_event)

    def apply_default_penalty(self, agent_id: AgentID, tick: int) -> None:
        agent = self.agent_registry.get_agent(agent_id)
        if not agent:
            logger.warning(f"JudicialSystem: Agent {agent_id} not found for penalty application.")
            return

        # Credit Freeze
        if isinstance(agent, ICreditFrozen):
            default_recovery = self.config_manager.get("finance.bank_defaults.credit_recovery_ticks", 100)
            jail_ticks = self.config_manager.get("bank.credit_recovery_ticks", default_recovery)
            agent.credit_frozen_until_tick = tick + jail_ticks
            logger.info(f"JudicialSystem: Credit frozen for Agent {agent_id} until tick {agent.credit_frozen_until_tick}.")

        # XP Penalty
        if isinstance(agent, IEducated):
            default_penalty = self.config_manager.get("finance.bank_defaults.bankruptcy_xp_penalty", 0.2)
            xp_penalty = self.config_manager.get("bank.bankruptcy_xp_penalty", default_penalty)
            # XP is float, so this is fine
            agent.education_xp *= (1.0 - xp_penalty)
            logger.info(f"JudicialSystem: Applied XP penalty to Agent {agent_id}.")

    def assess_solvency(self, agent_id: AgentID) -> bool:
        """
        Check if an agent is solvent based on SSoT balances.
        For now, simply checks if balance is non-negative.
        """
        balance = self.settlement_system.get_balance(agent_id, DEFAULT_CURRENCY)
        return balance >= 0

    def handle_default(self, event: LoanDefaultedEvent) -> SeizureResultDTO:
        agent_id = event['agent_id']
        creditor_id = event['creditor_id']
        amount = int(event['defaulted_amount']) # Ensure int
        loan_id = event['loan_id']
        tick = event['tick']

        result = SeizureResultDTO(
            seized_cash=0,
            seized_stocks_value=0,
            seized_inventory_value=0,
            remaining_debt=amount,
            is_fully_recovered=False,
            liquidated_assets={}
        )

        agent = self.agent_registry.get_agent(agent_id)
        if not agent:
            return result

        memo_base = f"Seizure: Default {loan_id}"

        # Stage 1: Cash Seizure (Direct from SSoT)
        debtor_balance = self.settlement_system.get_balance(agent_id, DEFAULT_CURRENCY)
        cash_seize_amount = min(debtor_balance, result.remaining_debt)

        # Get creditor agent object (agent is already fetched)
        creditor = self.agent_registry.get_agent(creditor_id)

        if cash_seize_amount > 0 and creditor:
            success = self.settlement_system.transfer(
                debit_agent=agent,
                credit_agent=creditor,
                amount=cash_seize_amount,
                memo=f"{memo_base} (Cash Stage 1)",
                tick=tick
            )
            if success:
                result.seized_cash += cash_seize_amount
                result.remaining_debt -= cash_seize_amount

        if result.remaining_debt <= 0:
             result.is_fully_recovered = True
             return result

        # Stage 2: Stocks
        if isinstance(agent, IPortfolioHandler):
            portfolio = agent.get_portfolio()
            for asset in portfolio.assets:
                if asset.asset_type == 'stock':
                    try:
                        firm_id = int(asset.asset_id)
                        quantity = asset.quantity
                        if self.shareholder_registry and quantity > 0:
                            # Transfer logic
                            # 1. Remove from Debtor
                            self.shareholder_registry.register_shares(firm_id, agent_id, 0)

                            # 2. Add to Creditor
                            current_holdings = self.shareholder_registry.get_shareholders_of_firm(firm_id)
                            creditor_qty = 0.0
                            for holding in current_holdings:
                                if holding['agent_id'] == creditor_id:
                                    creditor_qty = holding['quantity']
                                    break

                            self.shareholder_registry.register_shares(firm_id, creditor_id, creditor_qty + quantity)
                            logger.info(f"JudicialSystem: Transferred {quantity} shares of Firm {firm_id} from {agent_id} to {creditor_id}.")

                            # Note: We are not valuing the stocks here to reduce debt because stock valuation is complex
                            # and might not be accepted at face value by creditor in this simplified logic.
                            # Ideally we would get market price and reduce remaining_debt.

                    except ValueError:
                        pass
            agent.clear_portfolio()

        # Stage 3: Inventory (Liquidation)
        if result.remaining_debt > 0 and isinstance(agent, ILiquidatable):
             # This converts inventory to cash
             _ = agent.liquidate_assets(tick)

             # Now seize the generated cash from SSoT
             # We need to check balance again because liquidation increased it
             new_balance = self.settlement_system.get_balance(agent_id, DEFAULT_CURRENCY)
             # The available cash to seize is whatever is there now
             cash_seize_amount_2 = min(new_balance, result.remaining_debt)

             if cash_seize_amount_2 > 0 and creditor:
                 success = self.settlement_system.transfer(
                    debit_agent=agent,
                    credit_agent=creditor,
                    amount=cash_seize_amount_2,
                    memo=f"{memo_base} (Inventory Stage 3)",
                    tick=tick
                 )
                 if success:
                     result.seized_inventory_value += cash_seize_amount_2
                     result.remaining_debt -= cash_seize_amount_2

        if result.remaining_debt <= 0:
            result.is_fully_recovered = True
        else:
            # Emit DebtRestructuringRequiredEvent
            restructure_event = DebtRestructuringRequiredEvent(
                event_type="DEBT_RESTRUCTURING_REQUIRED",
                tick=tick,
                debtor_id=agent_id,
                remaining_debt=result.remaining_debt,
                creditor_id=creditor_id,
                loan_id=loan_id
            )
            self.event_bus.publish(restructure_event) # type: ignore
            logger.warning(f"JudicialSystem: Debt Restructuring Required for Agent {agent_id}. Remaining Debt: {result.remaining_debt}")

        return result
