from _typeshed import Incomplete
from modules.household.api import INeedsEngine as INeedsEngine, NeedsInputDTO as NeedsInputDTO, NeedsOutputDTO as NeedsOutputDTO, PrioritizedNeed as PrioritizedNeed
from modules.household.dtos import BioStateDTO as BioStateDTO

logger: Incomplete

class NeedsEngine(INeedsEngine):
    """
    Stateless engine managing need decay, satisfaction from durable assets, and need prioritization.
    Logic migrated from SocialComponent/PsychologyComponent.
    """
    def evaluate_needs(self, input_dto: NeedsInputDTO) -> NeedsOutputDTO: ...
