from _typeshed import Incomplete
from modules.tools.stub_generator.api import IStubGenerator as IStubGenerator, StubGenerationRequestDTO as StubGenerationRequestDTO, StubGenerationResultDTO as StubGenerationResultDTO

logger: Incomplete

class StubGenerator(IStubGenerator):
    """
    Implementation of IStubGenerator using mypy's stubgen.
    """
    def generate_stub(self, request: StubGenerationRequestDTO) -> StubGenerationResultDTO: ...
    def batch_generate(self, requests: list[StubGenerationRequestDTO]) -> list[StubGenerationResultDTO]: ...
