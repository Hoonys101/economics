from _internal.scripts.core.context_injector.api import ContextNodeDTO, IContextInjectorService, IContextStrategy, InjectionRequestDTO as InjectionRequestDTO, InjectionResultDTO
from _typeshed import Incomplete
from modules.tools.stub_generator.api import IStubGenerator as IStubGenerator

logger: Incomplete
HUB_FILES_BLACKLIST: Incomplete

class DependencyGraphStrategy(IContextStrategy):
    """
    AST-based strategy to discover structural dependencies.
    Implements Hub-Blocking to prevent fan-out explosion.
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

class ReviewWorkerStrategy(IContextStrategy):
    strategies: Incomplete
    def __init__(self) -> None: ...
    def resolve(self, request: InjectionRequestDTO, current_nodes: set[str]) -> list[ContextNodeDTO]: ...

class SpecWorkerStrategy(IContextStrategy):
    strategies: Incomplete
    def __init__(self) -> None: ...
    def resolve(self, request: InjectionRequestDTO, current_nodes: set[str]) -> list[ContextNodeDTO]: ...

class AuditWorkerStrategy(IContextStrategy):
    strategies: Incomplete
    def __init__(self) -> None: ...
    def resolve(self, request: InjectionRequestDTO, current_nodes: set[str]) -> list[ContextNodeDTO]: ...

class ContextInjectorService(IContextInjectorService):
    stub_generator: IStubGenerator
    stub_output_root: str
    def __init__(self) -> None: ...
    def analyze_context(self, request: InjectionRequestDTO) -> InjectionResultDTO: ...
