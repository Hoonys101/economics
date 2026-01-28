
from simulation.dtos import MacroFinancialContext
from simulation.decisions.portfolio_manager import PortfolioManager

def test_portfolio_optimization_under_stagflation():
    """
    Integration test to verify that a household reduces equity allocation
    under stagflation conditions.
    """
    # 1. Setup
    total_assets = 10000.0
    risk_aversion = 1.0
    risk_free_rate = 0.02
    equity_return_proxy = 0.08
    survival_cost = 300.0
    inflation_expectation = 0.02

    # 2. Optimize under normal conditions
    normal_context = MacroFinancialContext(
        inflation_rate=0.02,
        gdp_growth_rate=0.03,
        market_volatility=0.1,
        interest_rate_trend=0.0
    )

    target_cash_normal, target_deposit_normal, target_equity_normal = PortfolioManager.optimize_portfolio(
        total_liquid_assets=total_assets,
        risk_aversion=risk_aversion,
        risk_free_rate=risk_free_rate,
        equity_return_proxy=equity_return_proxy,
        survival_cost=survival_cost,
        inflation_expectation=inflation_expectation,
        macro_context=normal_context
    )

    # 3. Optimize under stagflation conditions
    stagflation_context = MacroFinancialContext(
        inflation_rate=0.10,
        gdp_growth_rate=-0.02,
        market_volatility=0.3,
        interest_rate_trend=0.01
    )

    target_cash_stag, target_deposit_stag, target_equity_stag = PortfolioManager.optimize_portfolio(
        total_liquid_assets=total_assets,
        risk_aversion=risk_aversion,
        risk_free_rate=risk_free_rate,
        equity_return_proxy=equity_return_proxy,
        survival_cost=survival_cost,
        inflation_expectation=inflation_expectation,
        macro_context=stagflation_context
    )

    # 4. Assert that equity allocation is lower under stagflation
    assert target_equity_stag < target_equity_normal

    # Also assert that safety preference (cash + deposit) is higher
    safety_assets_normal = target_cash_normal + target_deposit_normal
    safety_assets_stag = target_cash_stag + target_deposit_stag
    assert safety_assets_stag > safety_assets_normal
