from _internal.registry.api import ICommand as ICommand, IFixedCommandRegistry
from _typeshed import Incomplete

class FixedCommandRegistry(IFixedCommandRegistry):
    """
    Registry for code-defined system commands.
    Provides O(1) lookup for critical tools.
    """
    def __init__(self) -> None: ...
    def register(self, command: ICommand) -> None: ...
    def get_command(self, name: str) -> ICommand | None: ...
    def list_commands(self) -> list[str]: ...
    def has_command(self, name: str) -> bool: ...

def bootstrap_fixed_registry(registry: IFixedCommandRegistry):
    """Registers all system commands into the registry."""

fixed_registry: Incomplete
