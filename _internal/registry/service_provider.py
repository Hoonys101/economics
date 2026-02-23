from typing import Any, Optional
from _internal.registry.api import CommandContext, IServiceProvider

class LazyServiceProvider(IServiceProvider):
    """
    Provides lazy access to MissionRegistryServices to prevent 
    unnecessary JSON loading and circular imports.
    """
    def __init__(self, context: CommandContext):
        self._ctx = context
        self._gemini_service: Optional[Any] = None
        self._jules_service: Optional[Any] = None

    def get_gemini_service(self) -> Any:
        if not self._gemini_service:
            # Lazy import to avoid circular dependency and eager side-effects
            from _internal.registry.service import MissionRegistryService
            self._gemini_service = MissionRegistryService(db_path=self._ctx.gemini_registry_json)
        return self._gemini_service

    def get_jules_service(self) -> Any:
        if not self._jules_service:
            # Lazy import
            from _internal.registry.service import MissionRegistryService
            self._jules_service = MissionRegistryService(db_path=self._ctx.jules_registry_json)
        return self._jules_service
