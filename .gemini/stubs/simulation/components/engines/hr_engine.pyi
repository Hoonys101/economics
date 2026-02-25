from _typeshed import Incomplete
from modules.firm.api import HRContextDTO, HRDecisionInputDTO as HRDecisionInputDTO, HRDecisionOutputDTO, HRIntentDTO, IHRDepartment, IHREngine, ObligationDTO, PayrollIntentDTO
from modules.hr.api import IEmployeeDataProvider as IEmployeeDataProvider
from modules.simulation.dtos.api import FirmConfigDTO as FirmConfigDTO, FirmStateDTO as FirmStateDTO
from modules.system.api import CurrencyCode as CurrencyCode, MarketContextDTO as MarketContextDTO
from simulation.components.state.firm_state_models import HRState as HRState
from simulation.dtos.hr_dtos import EmployeeUpdateDTO as EmployeeUpdateDTO, HRPayrollContextDTO as HRPayrollContextDTO, HRPayrollResultDTO as HRPayrollResultDTO
from simulation.models import Order as Order, Transaction as Transaction

logger: Incomplete

class HREngine(IHREngine, IHRDepartment):
    """
    Stateless Engine for HR operations.
    Manages employees, calculates wages (skill + halo), and handles insolvency firing.
    """
    def decide_workforce(self, context: HRContextDTO) -> HRIntentDTO:
        """
        Pure function: HRContextDTO -> HRIntentDTO.
        Decides on hiring/firing targets and wage updates.
        """
    def manage_workforce(self, input_dto: HRDecisionInputDTO) -> HRDecisionOutputDTO:
        """
        Decides on hiring and firing based on production needs and budget constraints.
        Delegates to decide_workforce for core logic.
        """
    def calculate_wage(self, employee: IEmployeeDataProvider, base_wage: int, config: FirmConfigDTO) -> int:
        """
        Calculates wage based on skill and halo effect. Returns int pennies.
        """
    def calculate_payroll_obligations(self, hr_state: HRState, context: HRPayrollContextDTO, config: FirmConfigDTO) -> PayrollIntentDTO:
        """
        Calculates all payroll obligations (Wages, Taxes, Severance) without applying them.
        Returns a PayrollIntentDTO containing a list of ObligationDTOs.
        """
    def apply_payroll(self, hr_state: HRState, context: HRPayrollContextDTO, approved_obligations: list[ObligationDTO]) -> HRPayrollResultDTO:
        """
        Executes approved payroll obligations.
        Generates transactions and updates employee state.
        """
    def process_payroll(self, hr_state: HRState, context: HRPayrollContextDTO, config: FirmConfigDTO) -> HRPayrollResultDTO:
        """
        Processes payroll and returns a DTO with transactions and employee updates.
        This method MUST NOT have external side-effects.
        """
    def hire(self, hr_state: HRState, employee: IEmployeeDataProvider, wage: int, current_tick: int = 0): ...
    def remove_employee(self, hr_state: HRState, employee: IEmployeeDataProvider): ...
    def create_fire_transaction(self, hr_state: HRState, firm_id: int, wallet_balance: int, employee_id: int, severance_pay: int, current_time: int) -> Transaction | None:
        """
        Creates a severance transaction to fire an employee.
        Does NOT execute transfer or remove employee.
        """
    def finalize_firing(self, hr_state: HRState, employee_id: int):
        """
        Removes employee from state.
        Should be called after successful severance payment and employee.quit().
        """
