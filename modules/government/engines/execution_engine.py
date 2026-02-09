from typing import Any, List, Dict, Optional
import logging
from modules.government.api import IPolicyExecutionEngine, GovernmentExecutionContext, GovernmentStateDTO, PolicyDecisionDTO, ExecutionResultDTO
from modules.government.dtos import PaymentRequestDTO, BailoutResultDTO
from simulation.ai.enums import PolicyActionTag
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY
from simulation.dtos.api import MarketSnapshotDTO

logger = logging.getLogger(__name__)

class PolicyExecutionEngine(IPolicyExecutionEngine):
    """
    Stateless engine that translates policy decisions into concrete actions.
    Uses TaxService, WelfareManager, etc.
    """

    def execute(
        self,
        decision: PolicyDecisionDTO,
        current_state: GovernmentStateDTO,
        agents: List[Any],
        market_data: Dict[str, Any],
        context: GovernmentExecutionContext
    ) -> ExecutionResultDTO:
        """
        Executes a policy decision.
        """
        result = ExecutionResultDTO()

        # 1. Update State based on decision parameters (e.g. Tax Rate)
        if decision.parameters:
            if "income_tax_rate" in decision.parameters:
                result.state_updates["income_tax_rate"] = decision.parameters["income_tax_rate"]
            if "corporate_tax_rate" in decision.parameters:
                result.state_updates["corporate_tax_rate"] = decision.parameters["corporate_tax_rate"]
            if "welfare_budget_multiplier" in decision.parameters:
                result.state_updates["welfare_budget_multiplier"] = decision.parameters["welfare_budget_multiplier"]
            if "potential_gdp" in decision.parameters:
                result.state_updates["potential_gdp"] = decision.parameters["potential_gdp"]
            if "fiscal_stance" in decision.parameters:
                result.state_updates["fiscal_stance"] = decision.parameters["fiscal_stance"]

            # AdaptiveGovBrain uses 'rate_delta' or 'multiplier_delta'
            if "multiplier_delta" in decision.parameters:
                 new_mult = current_state.welfare_budget_multiplier + decision.parameters["multiplier_delta"]
                 result.state_updates["welfare_budget_multiplier"] = max(0.1, new_mult) # Clamp

            if "rate_delta" in decision.parameters:
                 action_type = decision.metadata.get("action_type", "")
                 if action_type == "ADJUST_CORP_TAX":
                     new_rate = current_state.corporate_tax_rate + decision.parameters["rate_delta"]
                     result.state_updates["corporate_tax_rate"] = max(0.05, min(0.6, new_rate))
                 elif action_type == "ADJUST_INCOME_TAX":
                     new_rate = current_state.income_tax_rate + decision.parameters["rate_delta"]
                     result.state_updates["income_tax_rate"] = max(0.05, min(0.6, new_rate))

        # 2. Execute Specific Logic based on Action Tag
        if decision.action_tag == PolicyActionTag.SOCIAL_POLICY:
             self._execute_social_policy(current_state, agents, market_data, context, result)

        elif decision.action_tag == PolicyActionTag.FIRM_BAILOUT:
             self._execute_firm_bailout(decision, current_state, agents, context, result)

        elif decision.action_tag == PolicyActionTag.INFRASTRUCTURE_INVESTMENT:
             self._execute_infrastructure_investment(current_state, context, result)

        return result

    def _execute_social_policy(
        self,
        state: GovernmentStateDTO,
        agents: List[Any],
        market_data: Dict[str, Any],
        context: GovernmentExecutionContext,
        result: ExecutionResultDTO
    ):
        """
        Orchestrates Tax Collection and Welfare Distribution.
        """
        # Convert market_data for services
        snapshot = MarketSnapshotDTO(
            tick=state.tick,
            market_signals={},
            market_data=market_data
        )

        # 1. Wealth Tax Logic (TaxService)
        # Note: TaxService.collect_wealth_tax returns TaxCollectionResultDTO with payment requests
        tax_result = context.tax_service.collect_wealth_tax(agents)
        result.payment_requests.extend(tax_result.payment_requests)

        # 2. Welfare Check (WelfareManager)
        # We need gdp_history for welfare logic (e.g. means testing relative to GDP?)
        # Pass state.gdp_history
        welfare_result = context.welfare_manager.run_welfare_check(
            agents,
            snapshot,
            state.tick,
            state.gdp_history,
            state.welfare_budget_multiplier
        )
        result.payment_requests.extend(welfare_result.payment_requests)

        # Funding Logic for Welfare is handled by Orchestrator upon receiving payment requests?
        # No, Orchestrator should check if funds are available and issue bonds if needed.
        # But wait, `Government` legacy code did bond issuance INSIDE `execute_social_policy`.
        # Here we return PaymentRequests. The Orchestrator must handle the funding check before executing them.

    def _execute_firm_bailout(
        self,
        decision: PolicyDecisionDTO,
        state: GovernmentStateDTO,
        agents: List[Any],
        context: GovernmentExecutionContext,
        result: ExecutionResultDTO
    ):
        firm_id = decision.parameters.get("firm_id")
        amount = decision.parameters.get("amount", 0.0)

        firm = next((a for a in agents if a.id == firm_id), None)
        if not firm:
            return

        # Check solvency via FinanceSystem (context)
        is_solvent = context.finance_system.evaluate_solvency(firm, state.tick)

        bailout_res = context.welfare_manager.provide_firm_bailout(firm, amount, state.tick, is_solvent)
        if bailout_res:
             result.bailout_results.append(bailout_res)

             # Execute the loan via FinanceSystem (Logic moved from Orchestrator)
             # Note: grant_bailout_loan returns (loan, transactions)
             if context.finance_system:
                 loan, txs = context.finance_system.grant_bailout_loan(firm, amount, state.tick)
                 if loan:
                     result.executed_loans.append(loan)
                 if txs:
                     result.transactions.extend(txs)

             # Asset Recovery Hook: If insolvent, notify PublicManager (if bailout terms require asset collateral)
             # But bailout usually implies trying to save.
             # If we had Logic for "Partial Nationalization", we'd use PublicManager here.
             # For now, just ensuring integration point exists.
             if not is_solvent and context.public_manager:
                 # Potentially signal public manager?
                 pass

    def _execute_infrastructure_investment(
        self,
        state: GovernmentStateDTO,
        context: GovernmentExecutionContext,
        result: ExecutionResultDTO
    ):
        if context.infrastructure_manager:
            # InfrastructureManager returns Transactions directly in legacy code.
            # We should probably adapt it to return PaymentRequests if possible.
            # But InfrastructureManager takes `households` to distribute wages?
            # If so, we need households list.
            # `execute` receives `agents`. We can filter households.
            pass
            # For now, let's assume infrastructure manager is called by orchestrator directly
            # or wrapped here if we pass households.
            # Since `agents` list is available, we can filter.
            pass
