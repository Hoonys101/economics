from _typeshed import Incomplete
from modules.household.api import ISocialEngine as ISocialEngine, SocialInputDTO as SocialInputDTO, SocialOutputDTO as SocialOutputDTO
from modules.household.dtos import SocialStateDTO as SocialStateDTO
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY
from simulation.ai.enums import Personality as Personality

logger: Incomplete
STANCE_BLUE: float
STANCE_RED: float
SURVIVAL_NEED_SCALE: float
TRUST_EMA_ALPHA: float
APPROVAL_WEIGHT_SATISFACTION: float
APPROVAL_WEIGHT_MATCH: float
TRUST_THRESHOLD: float
APPROVAL_THRESHOLD: float

class SocialEngine(ISocialEngine):
    """
    Stateless engine managing social status, political opinion, and other social metrics.
    Logic migrated from SocialComponent/PoliticalComponent.
    """
    def update_status(self, input_dto: SocialInputDTO) -> SocialOutputDTO: ...
