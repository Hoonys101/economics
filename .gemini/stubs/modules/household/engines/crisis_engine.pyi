from modules.household.api import ICrisisEngine as ICrisisEngine, PanicSellingInputDTO as PanicSellingInputDTO, PanicSellingResultDTO as PanicSellingResultDTO

class CrisisEngine(ICrisisEngine):
    """
    Stateless engine for handling household crisis situations (e.g. panic selling).
    """
    def evaluate_distress(self, input_dto: PanicSellingInputDTO) -> PanicSellingResultDTO: ...
