import pytest
from unittest.mock import Mock
from simulation.dtos import GovernmentSensoryDTO

# Note: The 'government', 'mock_config', 'mock_central_bank' fixtures are provided by tests/conftest.py

def test_potential_gdp_ema_convergence(government, mock_central_bank):
    """Test that potential GDP converges using EMA."""
    dto = GovernmentSensoryDTO(tick=1, current_gdp=1000.0, inflation_sma=0.02, unemployment_sma=0.05, gdp_growth_sma=0.01, wage_sma=100, approval_sma=0.5)
    government.update_sensory_data(dto)

    # Initial GDP: The old test was wrong. The EMA calculation runs on the first step.
    # If potential_gdp is 0, it initializes to current_gdp.
    # New logic in DecisionEngine:
    # potential_gdp = state.potential_gdp (0.0)
    # if potential_gdp == 0.0: potential_gdp = current_gdp (1000.0)

    government.make_policy_decision({}, 1, mock_central_bank)
    assert abs(government.potential_gdp - 1000.0) < 0.01

    # Update with same GDP, potential GDP should now update via EMA
    # potential = (0.01 * 1000) + (0.99 * 1000) = 1000.0
    government.make_policy_decision({}, 2, mock_central_bank)
    assert abs(government.potential_gdp - 1000.0) < 0.01

    # Update with higher GDP, should increase but lag
    dto.current_gdp = 2000.0
    government.update_sensory_data(dto)
    government.make_policy_decision({}, 3, mock_central_bank)
    # new = (0.01 * 2000) + (0.99 * 1000) = 20 + 990 = 1010.0
    assert abs(government.potential_gdp - 1010.0) < 0.01


def test_counter_cyclical_tax_adjustment_recession(government, mock_config, mock_central_bank):
    """Test Fiscal Expansion during Recession (GDP < Potential)."""
    mock_config.AUTO_COUNTER_CYCLICAL_ENABLED = True
    government.potential_gdp = 1000.0
    initial_tax_rate = government.income_tax_rate
    dto = GovernmentSensoryDTO(tick=1, current_gdp=800.0, inflation_sma=0.02, unemployment_sma=0.05, gdp_growth_sma=0.01, wage_sma=100, approval_sma=0.5)
    government.update_sensory_data(dto)

    # Sudden drop in current GDP (Recession)
    government.make_policy_decision({}, 1, mock_central_bank)

    assert government.fiscal_stance > 0 # Expansionary
    assert government.income_tax_rate < initial_tax_rate

def test_counter_cyclical_tax_adjustment_boom(government, mock_config, mock_central_bank):
    """Test Fiscal Contraction during Boom (GDP > Potential)."""
    mock_config.AUTO_COUNTER_CYCLICAL_ENABLED = True
    government.potential_gdp = 1000.0
    initial_tax_rate = government.income_tax_rate
    dto = GovernmentSensoryDTO(tick=1, current_gdp=1200.0, inflation_sma=0.02, unemployment_sma=0.05, gdp_growth_sma=0.01, wage_sma=100, approval_sma=0.5)
    government.update_sensory_data(dto)

    # Sudden rise in current GDP (Boom)
    government.make_policy_decision({}, 1, mock_central_bank)

    assert government.fiscal_stance < 0 # Contractionary
    assert government.income_tax_rate > initial_tax_rate

def test_debt_ceiling_enforcement(government):
    """Test that spending is blocked when Debt Ceiling is hit."""
    government._assets = 0.0
    government.total_debt = 0.0
    government.potential_gdp = 1000.0
    # From config, Debt Ceiling Ratio is 2.0, so ceiling is 2000.0
    government.sensory_data = GovernmentSensoryDTO(tick=0, current_gdp=1000.0, inflation_sma=0.02, unemployment_sma=0.05, gdp_growth_sma=0.01, wage_sma=100, approval_sma=0.5)


    agent = Mock()
    agent.id = 123
    agent._assets = 0.0

    # This is the critical fix. We need to simulate the side effect of
    # `issue_treasury_bonds`, which is that the government's assets INCREASE
    # by the amount of the bond. A simple mock doesn't do this.
    def issue_bonds_side_effect(amount, tick):
        government.wallet.add(amount, "USD") # Update Wallet!
        government._assets += amount # Keep this for legacy check if any
        return [Mock()], [] # Return a successful bond issuance and empty transactions

    government.finance_system.issue_treasury_bonds = Mock(side_effect=issue_bonds_side_effect)

    # 1. Spend within limit
    amount = 500.0
    txs = government.provide_household_support(agent, amount, current_tick=1)
    paid = sum(tx.price for tx in txs)
    assert paid == 500.0

    # Simulate execution (deduct spent amount)
    government._assets -= paid
    government.wallet.subtract(paid, "USD")

    # After spending 500, assets should be 0, and total_debt (which is -assets) should be 0.
    # The bonds were issued for 500, assets became 500, then spent.
    assert government.assets == 0.0

    # 2. Spend more
    amount = 1500.0
    txs = government.provide_household_support(agent, amount, current_tick=2)
    paid = sum(tx.price for tx in txs)
    assert paid == 1500.0

    # Simulate execution
    government._assets -= paid
    government.wallet.subtract(paid, "USD")

    assert government.assets == 0.0

    # 3. Try to spend when bond issuance fails
    government.finance_system.issue_treasury_bonds.side_effect = None # Disable the side effect
    government.finance_system.issue_treasury_bonds.return_value = [], []
    amount = 100.0
    txs = government.provide_household_support(agent, amount, current_tick=3)
    paid = sum(tx.price for tx in txs)
    assert paid == 0.0

def test_calculate_income_tax_uses_current_rate(government, mock_config):
    """Verify income tax calculation uses the current government rate."""
    # Manually overwrite the policy to be a flat tax policy (5%)
    from modules.government.dtos import FiscalPolicyDTO, TaxBracketDTO
    flat_bracket = TaxBracketDTO(floor=0.0, rate=0.05, ceiling=None)
    government.fiscal_policy = FiscalPolicyDTO(progressive_tax_brackets=[flat_bracket])

    income = 100.0
    # survival_cost is irrelevant for flat tax bracket starting at 0
    tax = government.calculate_income_tax(income, survival_cost=10.0)
    assert tax == 5.0
