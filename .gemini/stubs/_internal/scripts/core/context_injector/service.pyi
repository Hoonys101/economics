from _typeshed import Incomplete
from modules.tools.context_injector.api import ContextNodeDTO, IContextInjectorService, IContextStrategy, InjectionRequestDTO as InjectionRequestDTO, InjectionResultDTO
from modules.tools.stub_generator.api import IStubGenerator as IStubGenerator

logger: Incomplete

class DependencyGraphStrategy(IContextStrategy):
    """
    AST-based strategy to discover structural dependencies.
    """
    def resolve(self, request: InjectionRequestDTO, current_nodes: set[str]) -> list[ContextNodeDTO]: ...

class TestContextStrategy(IContextStrategy):
    """
    Tier 3: Discovery of related tests and conftest.py fixtures.
    """
    def resolve(self, request: InjectionRequestDTO, current_nodes: set[str]) -> list[ContextNodeDTO]: ...

class DocumentationStrategy(IContextStrategy):
    """
    Tier 4: Pattern-based architectural manual injection.
    """
    def resolve(self, request: InjectionRequestDTO, current_nodes: set[str]) -> list[ContextNodeDTO]: ...

class UniversalContractStrategy(IContextStrategy):
    """
    Tier 1 strategy for mandatory core contracts.
    """
    def resolve(self, request: InjectionRequestDTO, current_nodes: set[str]) -> list[ContextNodeDTO]: ...

class ContextInjectorService(IContextInjectorService):
    strategies: list[IContextStrategy]
    stub_generator: IStubGenerator
    stub_output_root: str
    def __init__(self) -> None: ...
    def analyze_context(self, request: InjectionRequestDTO) -> InjectionResultDTO: ...
