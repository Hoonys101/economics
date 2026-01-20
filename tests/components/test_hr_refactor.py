import pytest
from unittest.mock import Mock
from simulation.components.hr_department import HRDepartment
from simulation.firms import Firm
from simulation.core_agents import Household

class TestHRDepartmentRefactor:
    @pytest.fixture
    def firm_a(self):
        firm = Mock(spec=Firm)
        firm.id = 1
        firm.hr = HRDepartment(firm) # Use real HR
        firm.config_module = Mock()
        firm.config_module.HALO_EFFECT = 0.0
        return firm

    @pytest.fixture
    def firm_b(self):
        firm = Mock(spec=Firm)
        firm.id = 2
        firm.hr = HRDepartment(firm)
        firm.config_module = Mock()
        firm.config_module.HALO_EFFECT = 0.0
        return firm

    @pytest.fixture
    def employee(self):
        emp = Mock(spec=Household)
        emp.id = 101 # Use primitive integer ID
        emp.labor_skill = 1.0
        emp.education_level = 0
        emp.employer_id = 1
        return emp

    def test_transfer_employee(self, firm_a, firm_b, employee):
        """Test transferring employee from Firm A to Firm B."""
        # Setup: Employee works at Firm A
        firm_a.hr.employees.append(employee)
        firm_a.hr.employee_wages[employee.id] = 15.0

        # Action
        firm_a.hr.transfer_employee(employee, firm_b)

        # Assertions
        assert employee not in firm_a.hr.employees
        assert employee.id not in firm_a.hr.employee_wages

        assert employee in firm_b.hr.employees
        # Note: If self.employee_wages.get(101) fails to return 15.0, it means
        # firm_a.hr.employee_wages was not correctly populated or accessed.
        # But we set it above.

        # Debug why previous test failed: firm_b.hr.hire might use default wage if not passed correctly?
        # firm_a.hr.transfer_employee passes: self.employee_wages.get(employee.id, 10.0)
        # If employee.id is a Mock, it might hash differently?
        # But here we set emp.id = 101 (int).

        assert firm_b.hr.employee_wages[employee.id] == 15.0 # Wage preserved

        assert employee.employer_id == firm_b.id
