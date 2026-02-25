import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(os.getcwd())))

from _internal.scripts.core.context_injector.service import ContextInjectorService
from _internal.scripts.core.context_injector.api import InjectionRequestDTO

injector = ContextInjectorService()
req = InjectionRequestDTO(
    target_files=[
        "reports/diagnostic_refined.md",
        "modules/finance/kernel/ledger.py",
        "simulation/world_state.py",
        "simulation/orchestration/tick_orchestrator.py",
        "modules/system/services/command_service.py",
        "simulation/initialization/initializer.py"
    ],
    worker_type="audit",
    include_tests=True,
    include_docs=True,
    max_dependency_depth=1
)

result = injector.analyze_context(req)
print(f"Total files injected: {result.total_files}")
for node in result.nodes:
    print(f"- {node.file_path} (Tier: {node.tier.name}, Stub: {node.is_stub})")
