from _typeshed import Incomplete
from modules.common.financial.dtos import Claim as Claim
from modules.finance.api import ITaxService as ITaxService
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY, IAgentRegistry as IAgentRegistry
from simulation.firms import Firm as Firm

class TaxService(ITaxService):
    agent_registry: Incomplete
    def __init__(self, agent_registry: IAgentRegistry) -> None: ...
    def calculate_liquidation_tax_claims(self, firm: Firm) -> list[Claim]: ...
