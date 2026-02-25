"""
Facade for Context Injector Service.
Moved to _internal/scripts/core/context_injector/service.py as per SSoT migration strategy.
"""
from _internal.scripts.core.context_injector.service import (
    DependencyGraphStrategy,
    TestContextStrategy,
    DocumentationStrategy,
    UniversalContractStrategy,
    ReviewWorkerStrategy,
    SpecWorkerStrategy,
    AuditWorkerStrategy,
    ContextInjectorService,
    HUB_FILES_BLACKLIST
)
