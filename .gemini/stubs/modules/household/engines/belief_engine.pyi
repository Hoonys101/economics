from collections import deque as deque
from modules.household.api import BeliefInputDTO as BeliefInputDTO, BeliefResultDTO as BeliefResultDTO, IBeliefEngine as IBeliefEngine

class BeliefEngine(IBeliefEngine):
    """
    Stateless engine for updating household beliefs about prices and inflation.
    """
    def update_beliefs(self, input_dto: BeliefInputDTO) -> BeliefResultDTO: ...
