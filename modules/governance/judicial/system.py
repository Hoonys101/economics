from typing import Dict, Any, Optional
import logging
from modules.common.config_manager.api import ConfigManager
from modules.events.dtos import FinancialEvent, LoanDefaultedEvent, DebtRestructuringRequiredEvent
from modules.system.event_bus.api import IEventBus
from modules.governance.judicial.api import IJudicialSystem, SeizureWaterfallResultDTO
from simulation.finance.api import ISettlementSystem
from modules.system.api import IAgentRegistry
from modules.finance.api import (
    IShareholderRegistry, IPortfolioHandler, ICreditFrozen, IFinancialEntity, IFinancialAgent, ILiquidatable
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

            # Execute Seizure Waterfall
            result = self.execute_seizure_waterfall(
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

        # 1. Share Seizure moved to execute_seizure_waterfall

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

    def _get_agent_balance(self, agent: Any) -> float:
        if isinstance(agent, IFinancialAgent):
            return agent.get_balance(DEFAULT_CURRENCY)
        elif isinstance(agent, IFinancialEntity):
            return agent.assets
        elif hasattr(agent, 'wallet'):
            return agent.wallet.get_balance(DEFAULT_CURRENCY)
        return 0.0

    def _transfer_cash(self, agent: Any, creditor: Any, amount: float, memo: str, tick: int) -> float:
        """Attempts to transfer amount. Returns actual transferred amount."""
        balance = self._get_agent_balance(agent)
        transfer_amount = min(balance, amount)

        if transfer_amount <= 0:
            return 0.0

        success = self.settlement_system.transfer(
            debit_agent=agent,
            credit_agent=creditor,
            amount=transfer_amount,
            memo=memo,
            tick=tick
        )

        return transfer_amount if success else 0.0

    def execute_seizure_waterfall(self, agent_id: int, creditor_id: int, amount: float, loan_id: str, tick: int) -> SeizureWaterfallResultDTO:
        agent = self.agent_registry.get_agent(agent_id)
        creditor = self.agent_registry.get_agent(creditor_id)

        result = SeizureWaterfallResultDTO(
            success=False,
            total_seized=0.0,
            remaining_debt=amount,
            cash_seized=0.0,
            stocks_seized_value=0.0,
            inventory_seized_value=0.0
        )

        if not agent or not creditor:
            return result

        memo_base = f"Seizure: Default {loan_id}"

        # Stage 1: Cash
        cash_1 = self._transfer_cash(agent, creditor, result.remaining_debt, f"{memo_base} (Cash Stage 1)", tick)
        result.cash_seized += cash_1
        result.total_seized += cash_1
        result.remaining_debt -= cash_1

        if result.remaining_debt <= 0.001: # Epsilon check
             result.success = True
             return result

        # Stage 2: Stocks
        if isinstance(agent, IPortfolioHandler):
            portfolio = agent.get_portfolio()
            # We assume stocks don't immediately reduce debt value (valuation issue),
            # but we transfer them to creditor to prevent leakage.
            for asset in portfolio.assets:
                if asset.asset_type == 'stock':
                    try:
                        firm_id = int(asset.asset_id)
                        quantity = asset.quantity
                        if self.shareholder_registry and quantity > 0:
                            # 1. Remove from Debtor
                            self.shareholder_registry.register_shares(firm_id, agent_id, 0)

                            # 2. Add to Creditor (Need to fetch existing shares first)
                            # Assuming shareholder_registry can handle this or we just re-register
                            # Since we don't have atomic 'transfer_shares', we do best effort.
                            # Ideally we get creditor shares first.
                            current_holdings = self.shareholder_registry.get_shareholders_of_firm(firm_id)
                            creditor_qty = 0.0
                            for holding in current_holdings:
                                if holding['agent_id'] == creditor_id:
                                    creditor_qty = holding['quantity']
                                    break

                            self.shareholder_registry.register_shares(firm_id, creditor_id, creditor_qty + quantity)
                            # Note: We don't increment result.stocks_seized_value because we don't know the price.
                            # And we don't reduce remaining_debt.
                            logger.info(f"JudicialSystem: Transferred {quantity} shares of Firm {firm_id} from {agent_id} to {creditor_id}.")

                    except ValueError:
                        pass
            agent.clear_portfolio()

        # Stage 3: Inventory (Liquidation)
        # Check remaining debt again (stocks didn't reduce it)
        if result.remaining_debt > 0.001 and isinstance(agent, ILiquidatable):
             # This converts inventory to cash
             _ = agent.liquidate_assets(tick)

             # Now seize the generated cash
             cash_2 = self._transfer_cash(agent, creditor, result.remaining_debt, f"{memo_base} (Inventory Stage 3)", tick)
             result.inventory_seized_value += cash_2 # We assume cash obtained came from liquidation
             result.total_seized += cash_2
             result.remaining_debt -= cash_2

        if result.remaining_debt <= 0.001:
            result.success = True
        else:
            # Emit DebtRestructuringRequiredEvent
            event = DebtRestructuringRequiredEvent(
                event_type="DEBT_RESTRUCTURING_REQUIRED",
                tick=tick,
                agent_id=agent_id,
                remaining_debt=result.remaining_debt,
                creditor_id=creditor_id
            )
            self.event_bus.publish(event)
            logger.warning(f"JudicialSystem: Debt Restructuring Required for Agent {agent_id}. Remaining Debt: {result.remaining_debt}")

        return result
