from _typeshed import Incomplete
from modules.simulation.api import AgentCoreConfigDTO as AgentCoreConfigDTO, IAgent as IAgent
from modules.simulation.dtos.api import FirmConfigDTO as FirmConfigDTO
from modules.system.api import AgentID as AgentID
from simulation.engine import Simulation as Simulation
from simulation.firms import Firm as Firm
from simulation.systems.settlement_system import SettlementSystem as SettlementSystem

logger: Incomplete

class FirmFactory:
    """
    Handles atomic creation, registration, and initialization of Firms.
    Fixes TD-LIFECYCLE-GHOST-FIRM.
    """
    @staticmethod
    def create_and_register_firm(simulation: Simulation, instance_class: type['Firm'], core_config: AgentCoreConfigDTO, firm_config_dto: FirmConfigDTO, **kwargs) -> Firm | None:
        """
        Executes the Atomic Startup Sequence:
        1. Instantiate Firm.
        2. Register in Simulation.
        3. Open Bank Account (implicit via registration in Settlement indices).
        4. Transfer initial funds if provided in kwargs['initial_capital'].
        """
