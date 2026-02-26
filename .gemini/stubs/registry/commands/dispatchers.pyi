from _internal.registry.api import CommandContext as CommandContext, CommandResult, ICommand
from _internal.scripts.core.context import get_core_contract_paths as get_core_contract_paths, resolve_manual_links as resolve_manual_links
from _typeshed import Incomplete
from pathlib import Path as Path

logger: Incomplete

class GeminiDispatcher(ICommand):
    @property
    def name(self) -> str: ...
    @property
    def description(self) -> str: ...
    def execute(self, ctx: CommandContext) -> CommandResult: ...

class JulesDispatcher(ICommand):
    @property
    def name(self) -> str: ...
    @property
    def description(self) -> str: ...
    def execute(self, ctx: CommandContext) -> CommandResult: ...
