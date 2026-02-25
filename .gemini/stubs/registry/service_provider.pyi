from _internal.registry.api import CommandContext as CommandContext, IServiceProvider
from typing import Any

class LazyServiceProvider(IServiceProvider):
    """
    Provides lazy access to MissionRegistryServices to prevent 
    unnecessary JSON loading and circular imports.
    """
    def __init__(self, context: CommandContext) -> None: ...
    def get_gemini_service(self) -> Any: ...
    def get_jules_service(self) -> Any: ...
