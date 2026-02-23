from typing import Dict, List, Optional
from _internal.registry.api import ICommand, IFixedCommandRegistry

class FixedCommandRegistry(IFixedCommandRegistry):
    """
    Registry for code-defined system commands.
    Provides O(1) lookup for critical tools.
    """
    def __init__(self):
        self._commands: Dict[str, ICommand] = {}

    def register(self, command: ICommand) -> None:
        self._commands[command.name] = command

    def get_command(self, name: str) -> Optional[ICommand]:
        return self._commands.get(name)

    def list_commands(self) -> List[str]:
        return list(self._commands.keys())

    def has_command(self, name: str) -> bool:
        return name in self._commands

def bootstrap_fixed_registry(registry: IFixedCommandRegistry):
    """Registers all system commands into the registry."""
    from _internal.registry.commands.core import ResetCommand, HarvestCommand, SyncCommand
    from _internal.registry.commands.git import GitReviewCommand, MergeCommand
    from _internal.registry.commands.dispatchers import GeminiDispatcher, JulesDispatcher

    registry.register(ResetCommand())
    registry.register(HarvestCommand())
    registry.register(SyncCommand())
    registry.register(GitReviewCommand())
    registry.register(MergeCommand())
    registry.register(GeminiDispatcher())
    registry.register(JulesDispatcher())

# Global singleton for the fixed registry
fixed_registry = FixedCommandRegistry()
bootstrap_fixed_registry(fixed_registry)
