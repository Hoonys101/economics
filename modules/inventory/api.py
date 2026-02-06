from typing import Protocol, Any, Optional

class IInventoryHandler(Protocol):
    """Interface for managing the state of physical or digital assets."""
    def lock_asset(self, asset_id: Any, lock_owner_id: Any) -> bool:
        """Atomically places a lock on an asset, returns False if already locked."""
        ...

    def release_asset(self, asset_id: Any, lock_owner_id: Any) -> bool:
        """Releases a lock, returns False if not owned by the lock_owner_id."""
        ...

    def transfer_asset(self, asset_id: Any, new_owner_id: Any) -> bool:
        """Transfers ownership of the asset."""
        ...

    def add_lien(self, asset_id: Any, lien_details: Any) -> Optional[str]:
        """Adds a lien to a property, returns lien_id on success."""
        ...

    def remove_lien(self, asset_id: Any, lien_id: str) -> bool:
        """Removes a lien from a property."""
        ...
