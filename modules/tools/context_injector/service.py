
from typing import List, Set, Optional
import os
from modules.tools.context_injector.api import (
    IContextInjectorService, InjectionRequestDTO, InjectionResultDTO,
    ContextNodeDTO, ContextTier
)

class ContextInjectorService(IContextInjectorService):
    def analyze_context(self, request: InjectionRequestDTO) -> InjectionResultDTO:
        nodes = []
        missing = []

        for path in request.target_files:
            if os.path.exists(path):
                nodes.append(ContextNodeDTO(
                    file_path=path,
                    tier=ContextTier.STRUCTURAL,
                    description="Manual injection",
                    source_node="User Request"
                ))
            else:
                missing.append(path)

        return InjectionResultDTO(
            nodes=nodes,
            total_files=len(nodes),
            missing_files=missing,
            strategy_used="SimplePassthrough"
        )
