import pytest
from unittest.mock import MagicMock
from simulation.components.engines.hr_engine import HREngine
from simulation.components.state.firm_state_models import HRState
from simulation.dtos.hr_dtos import HRPayrollContextDTO, HRPayrollResultDTO, EmployeeUpdateDTO, TaxPolicyDTO
from modules.simulation.dtos.api import FirmConfigDTO
from modules.system.api import DEFAULT_CURRENCY
from modules.hr.api import IEmployeeDataProvider

@pytest.fixture
def hr_engine():
    return HREngine()

@pytest.fixture
def mock_employee():
    emp = MagicMock(spec=IEmployeeDataProvider)
    emp.id = 101
    emp.employer_id = 1
    emp.is_employed = True
    emp.labor_skill = 1.0
    emp.education_level = 0.0
    # Attributes that would be modified by side-effects (now should not be touched)
    emp.labor_income_this_tick = 0.0
    return emp

@pytest.fixture
def hr_state(mock_employee):
    state = HRState()
    state.employees = [mock_employee]
    state.employee_wages = {101: 20.0}
    return state

@pytest.fixture
def config():
    cfg = MagicMock(spec=FirmConfigDTO)
    cfg.halo_effect = 0.1
    cfg.ticks_per_year = 365
    cfg.severance_pay_weeks = 2.0
    return cfg

@pytest.fixture
def context():
    return HRPayrollContextDTO(
        exchange_rates={DEFAULT_CURRENCY: 1.0},
        tax_policy=TaxPolicyDTO(income_tax_rate=0.1, survival_cost=10.0, government_agent_id=999),
        current_time=100,
        firm_id=1,
        wallet_balances={DEFAULT_CURRENCY: 1000.0},
        labor_market_min_wage=10.0
    )

def test_process_payroll_solvent(hr_engine, hr_state, config, context, mock_employee):
    """Test standard payroll processing (solvent firm)."""
    result = hr_engine.process_payroll(hr_state, context, config)

    assert isinstance(result, HRPayrollResultDTO)
    assert len(result.transactions) == 2 # Wage + Tax
    assert len(result.employee_updates) == 1

    # Verify Wage Transaction
    tx_wage = next(t for t in result.transactions if t.transaction_type == "wage")
    assert tx_wage.buyer_id == 1
    assert tx_wage.seller_id == 101
    assert tx_wage.price == 18.0 # 20.0 wage - 10% tax on 20.0 = 18.0 (tax applies if > 10.0)

    # Verify Tax Transaction
    tx_tax = next(t for t in result.transactions if t.transaction_type == "tax")
    assert tx_tax.price == 2.0

    # Verify Employee Update
    update = result.employee_updates[0]
    assert update.employee_id == 101
    assert update.net_income == 18.0
    assert not update.fire_employee

    # Verify NO side effects on employee object
    assert mock_employee.labor_income_this_tick == 0.0 # Should remain 0, updated by Orchestrator
    mock_employee.quit.assert_not_called()

def test_process_payroll_insolvent_severance(hr_engine, hr_state, config, context, mock_employee):
    """Test firing due to insolvency (can afford severance)."""
    # Low balance, can pay severance (2 weeks = 40.0 approx? No, wage * weeks. Wage=20. Weeks=2. Severance=40.)
    # Balance = 50.0 (Can afford severance but maybe not wage? Wage is 20. Wait.)
    # Check logic:
    # if current_balance >= wage: Pay Wage
    # else if liquid >= wage: Zombie
    # else: Fire

    # Set balance to 10.0 (cannot afford wage 20.0)
    # Severance needed = 20.0 * 2 = 40.0.
    # If balance is 10.0, cannot afford severance. -> Zombie.

    # Let's set balance to 45.0. Can afford wage 20.0. So it will pay wage.
    # To trigger firing, we need total_liquid < wage.
    # But current_balance is liquid.
    # Ah, "Solvent but Illiquid -> Zombie". Logic:
    # if current_balance >= wage: Pay
    # elif total_liquid >= wage: Zombie (assets exist but not cash)
    # else: Fire (Insolvent)

    # So to fire, total_liquid < wage.
    # context.wallet_balances = {DEFAULT: 10.0}. Wage = 20.0.
    # Fire logic triggered.
    # Inside _handle_insolvency_transactions:
    # if current_balance >= severance_pay: Fire with Severance
    # else: Zombie

    # So we need Balance < Wage AND Balance >= Severance.
    # Wage = 20.
    # Severance = Wage * 2 = 40.
    # Impossible to have Balance < 20 AND Balance >= 40.

    # Wait, usually severance is weeks of pay. If 'wage' is daily/tickly?
    # If wage is per tick, and severance is in weeks?
    # Spec says: severance_pay = wage * severance_weeks.
    # If severance_weeks = 2.0 (ticks? or weeks?). If ticks, then 2 ticks of wage.
    # If wage is 20, severance is 40.
    # If I set severance_weeks = 0.5. Severance = 10.0.
    # Balance = 15.0. Wage = 20.0.
    # Balance < Wage (Can't pay wage).
    # Balance >= Severance (Can pay severance).

    config.severance_pay_weeks = 0.5
    context_low = HRPayrollContextDTO(
        exchange_rates={DEFAULT_CURRENCY: 1.0},
        tax_policy=None,
        current_time=100,
        firm_id=1,
        wallet_balances={DEFAULT_CURRENCY: 15.0}, # < 20, >= 10
        labor_market_min_wage=10.0
    )

    result = hr_engine.process_payroll(hr_state, context_low, config)

    assert len(result.transactions) == 1 # Severance
    assert result.transactions[0].transaction_type == "severance"
    assert result.transactions[0].price == 10.0

    assert len(result.employee_updates) == 1
    update = result.employee_updates[0]
    assert update.fire_employee is True
    assert update.severance_pay == 10.0

    # Verify NO side effects
    mock_employee.quit.assert_not_called()
    assert mock_employee in hr_state.employees # Not removed yet

def test_process_payroll_zombie(hr_engine, hr_state, config, context, mock_employee):
    """Test zombie state (cannot afford wage OR severance)."""
    # Balance = 5.0. Wage = 20.0. Severance = 40.0 (default 2 weeks).
    context_zombie = HRPayrollContextDTO(
        exchange_rates={DEFAULT_CURRENCY: 1.0},
        tax_policy=None,
        current_time=100,
        firm_id=1,
        wallet_balances={DEFAULT_CURRENCY: 5.0},
        labor_market_min_wage=10.0
    )

    result = hr_engine.process_payroll(hr_state, context_zombie, config)

    assert len(result.transactions) == 0
    assert len(result.employee_updates) == 0 # No income, no firing instruction (implicitly keep employed as zombie)

    # Check internal state mutation (allowed for zombie tracking)
    assert mock_employee.id in hr_state.unpaid_wages
    assert len(hr_state.unpaid_wages[mock_employee.id]) == 1
    assert hr_state.unpaid_wages[mock_employee.id][0] == (100, 20.0)

def test_process_payroll_context_immutability(hr_engine, hr_state, config, context, mock_employee):
    """Verify that process_payroll does NOT mutate context.wallet_balances."""
    initial_balance = context.wallet_balances[DEFAULT_CURRENCY]

    # Run payroll
    hr_engine.process_payroll(hr_state, context, config)

    # Check balance - should be unchanged in the DTO
    assert context.wallet_balances[DEFAULT_CURRENCY] == initial_balance
