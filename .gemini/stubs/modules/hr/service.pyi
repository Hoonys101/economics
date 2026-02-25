from modules.common.financial.dtos import Claim as Claim
from modules.hr.api import IHRService as IHRService
from simulation.firms import Firm as Firm

class HRService(IHRService):
    def calculate_liquidation_employee_claims(self, firm: Firm, current_tick: int) -> list[Claim]: ...
