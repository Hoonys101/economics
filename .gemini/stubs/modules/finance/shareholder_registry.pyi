from modules.finance.api import IShareholderRegistry as IShareholderRegistry, ShareholderData as ShareholderData

class ShareholderRegistry:
    """
    Centralized service for tracking corporate share ownership.
    Implements IShareholderRegistry protocol.
    Single source of truth for stock ownership, replacing scattered dictionaries.
    """
    def __init__(self) -> None: ...
    def register_shares(self, firm_id: int, agent_id: int, quantity: float) -> None:
        """
        Updates the share registry.
        If quantity is <= 0, the entry is removed to keep the registry clean.
        """
    def get_shareholders_of_firm(self, firm_id: int) -> list[ShareholderData]:
        """
        Returns a list of all current shareholders for a given firm.
        """
    def get_total_shares(self, firm_id: int) -> float:
        """
        Returns the total number of outstanding shares for a firm.
        """
    def clear(self) -> None:
        """Clears the entire registry."""
