from typing import Protocol, Any, runtime_checkable
from modules.government.dtos import IAgent

@runtime_checkable
class IWelfareRecipient(IAgent, Protocol):
    """
    Protocol for agents that can receive welfare benefits.
    Typically implemented by Household agents.
    """
    is_active: bool
    is_employed: bool
    needs: Any  # Marker for households in legacy logic
