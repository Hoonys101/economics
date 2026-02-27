from modules.government.dtos import IAgent as IAgent
from typing import Any, Protocol

class IWelfareRecipient(IAgent, Protocol):
    """
    Protocol for agents that can receive welfare benefits.
    Typically implemented by Household agents.
    """
    is_active: bool
    is_employed: bool
    needs: Any
