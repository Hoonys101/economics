from typing import Tuple, Dict
import math
from simulation.dtos import MacroFinancialContext

class PortfolioManager:
    """
    Implements the Rational Investor brain (WO-026).
    Maximizes Utility U = E(R) - lambda * sigma^2
    """

    # Constants for risk aversion calculation
    CONST_INFLATION_TARGET = 0.02
    INFLATION_STRESS_MULTIPLIER = 10.0
    RECESSION_STRESS_MULTIPLIER = 5.0
    INTEREST_RATE_STRESS_MULTIPLIER = 2.0
    TOTAL_STRESS_MULTIPLIER_CAP = 3.0

    @staticmethod
    def calculate_effective_risk_aversion(base_lambda: float, context: MacroFinancialContext) -> float:
        """
        Calculates an adjusted risk aversion based on the provided macroeconomic context.
        This logic is central to the WO-062 feature and now fully visible for review.
        """
        # 1. Inflation Stress (Fear increases when inflation exceeds the 2% target)
        inflation_excess = max(0.0, context.inflation_rate - PortfolioManager.CONST_INFLATION_TARGET)
        stress_inflation = inflation_excess * PortfolioManager.INFLATION_STRESS_MULTIPLIER

        # 2. Recession Stress (Fear increases sharply during negative growth)
        stress_recession = 0.0
        if context.gdp_growth_rate < 0.0:
            stress_recession = abs(context.gdp_growth_rate) * PortfolioManager.RECESSION_STRESS_MULTIPLIER

        # 3. Interest Rate Volatility (Optional)
        stress_rate = max(0.0, context.interest_rate_trend) * PortfolioManager.INTEREST_RATE_STRESS_MULTIPLIER

        total_stress_multiplier = 1.0 + stress_inflation + stress_recession + stress_rate

        # Apply a cap to prevent overly extreme aversion
        total_stress_multiplier = min(PortfolioManager.TOTAL_STRESS_MULTIPLIER_CAP, total_stress_multiplier)

        return base_lambda * total_stress_multiplier

    @staticmethod
    def optimize_portfolio(
        total_liquid_assets: float,
        risk_aversion: float,
        risk_free_rate: float,
        equity_return_proxy: float,
        survival_cost: float,
        inflation_expectation: float,
        macro_context: MacroFinancialContext = None
    ) -> Tuple[float, float, float]:
        """
        Calculates optimal allocation between Consumption(Cash), Risk-Free(Deposit), and Risky(Equity/Startup).

        Args:
            total_liquid_assets: Total available funds (Cash + Deposits).
            risk_aversion: Lambda (0.1 ~ 10.0).
            risk_free_rate: Annualized bank deposit rate (nominal).
            equity_return_proxy: Expected return on equity (e.g. Dividend Yield or Avg ROI).
            survival_cost: Monthly survival cost (Safety Margin base).
            inflation_expectation: Expected inflation rate.
            macro_context: MacroFinancialContext object.

        Returns:
            Tuple[float, float, float]: (Target Cash, Target Deposit, Target Equity Investment)
        """
        effective_risk_aversion = risk_aversion
        if macro_context:
            effective_risk_aversion = PortfolioManager.calculate_effective_risk_aversion(risk_aversion, macro_context)

        # 1. Safety Margin Logic (Cash/Risk-Free)
        # "Safety Margin: 3 months of survival cost... MUST be kept in Cash/Risk-Free Deposit"
        # Since Bank Deposit is risk-free and pays interest, a rational agent prefers Deposit over Cash
        # for the safety margin, except for immediate transactional needs (Cash).
        # We'll assume "Cash" is needed for 1 month of consumption, "Deposit" for the rest of safety margin + Investment.

        safety_margin_total = survival_cost * 3.0

        # Immediate Liquidity Need (Transaction Demand for Money)
        # Keep 1 month expenses in Cash (Wallet)
        target_cash = survival_cost * 1.0

        # The rest of safety margin goes to Deposit
        required_deposit_safety = max(0.0, safety_margin_total - target_cash)

        investable_surplus = total_liquid_assets - target_cash - required_deposit_safety

        target_deposit = required_deposit_safety
        target_equity = 0.0

        if investable_surplus <= 0:
            # Deficit: Only allocate what we have.
            # Priority: Cash > Deposit Safety
            if total_liquid_assets < target_cash:
                target_cash = total_liquid_assets
                target_deposit = 0.0
            else:
                target_deposit = total_liquid_assets - target_cash

            return target_cash, target_deposit, target_equity

        # 2. Surplus Allocation (Mpt-lite)
        # Compare Risk-Free Real Rate vs Equity Real Rate
        # r_f = risk_free_rate - inflation_expectation
        # r_e = equity_return_proxy - inflation_expectation
        # Utility U = E(R) - 0.5 * lambda * sigma^2 (Using 0.5 factor for standard mean-variance)
        # Wait, spec says: U = E(R) - lambda * sigma^2

        # We need Assumptions for Risk (Variance):
        # Sigma_Deposit ~= 0.0 (Risk Free)
        # Sigma_Equity ~= 0.2 (20% Volatility - assumption)
        sigma_equity_sq = 0.2 ** 2  # 0.04

        # Expected Utility of Deposit
        u_deposit = risk_free_rate # Variance is 0

        # Expected Utility of Equity
        # U_e = R_e - lambda * sigma^2
        u_equity = equity_return_proxy - (effective_risk_aversion * sigma_equity_sq)

        # Threshold Check
        # If U_equity > U_deposit, allocate portion to Equity.
        # How much? "Kelly Criterion" or simple heuristic?
        # Spec: "If R_equity > R_deposit + RiskPremium... allocate to Equity. Else, keep in Deposit."
        # This implies a binary switch or a partial allocation.
        # "Risk Loving agents attempt Startups more often."

        # Let's implement a continuous allocation based on the Utility Gap.
        # Log-odds or simple ratio?
        # Let's use a sigmoid-like or linear scale.

        risk_premium_required = effective_risk_aversion * sigma_equity_sq
        excess_return = equity_return_proxy - risk_free_rate

        if excess_return > risk_premium_required:
            # Attractive!
            # Allocation % = (E(R) - Rf) / (lambda * sigma^2)  <-- Merton's Portfolio Problem solution
            # optimal_equity_weight = excess_return / (effective_risk_aversion * sigma_equity_sq)

            # Avoid division by zero
            denom = max(0.0001, effective_risk_aversion * sigma_equity_sq)
            optimal_equity_weight = excess_return / denom

            # Cap at 1.0 (100% of surplus)
            optimal_equity_weight = min(1.0, max(0.0, optimal_equity_weight))

            target_equity = investable_surplus * optimal_equity_weight
            target_deposit += investable_surplus * (1.0 - optimal_equity_weight)
        else:
            # Not attractive, put everything in Deposit
            target_deposit += investable_surplus
            target_equity = 0.0

        return target_cash, target_deposit, target_equity
