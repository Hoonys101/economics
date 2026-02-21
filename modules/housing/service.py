from typing import Optional, List, Any, Dict, TYPE_CHECKING
from uuid import UUID
import logging

from modules.housing.api import IHousingService
from modules.inventory.api import IInventoryHandler
from modules.finance.api import LienDTO
from modules.common.interfaces import IPropertyOwner, IResident

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState
    from simulation.models import Transaction
    from simulation.core_agents import Household

logger = logging.getLogger(__name__)

class HousingService(IHousingService):
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger if logger else logging.getLogger(__name__)
        self.contract_locks: Dict[int, UUID] = {}
        self.real_estate_units: List[Any] = []

    def set_real_estate_units(self, units: List[Any]) -> None:
        self.real_estate_units = units

    def is_under_contract(self, property_id: int) -> bool:
        return property_id in self.contract_locks

    def set_under_contract(self, property_id: int, saga_id: UUID) -> bool:
        if property_id in self.contract_locks:
             return False
        self.contract_locks[property_id] = saga_id
        return True

    def release_contract(self, property_id: int, saga_id: UUID) -> bool:
        if self.contract_locks.get(property_id) == saga_id:
             del self.contract_locks[property_id]
             return True
        return False

    def lock_asset(self, asset_id: Any, lock_owner_id: Any) -> bool:
        return self.set_under_contract(int(asset_id), lock_owner_id)

    def release_asset(self, asset_id: Any, lock_owner_id: Any) -> bool:
        return self.release_contract(int(asset_id), lock_owner_id)

    def transfer_asset(self, asset_id: Any, new_owner_id: Any) -> bool:
        return self.transfer_ownership(int(asset_id), int(new_owner_id))

    def add_lien(self, property_id: int, loan_id: Any, lienholder_id: Optional[int] = None, principal: Optional[int] = None) -> Optional[str]:
        # Support for IInventoryHandler signature: add_lien(asset_id, lien_details)
        if isinstance(loan_id, dict) and lienholder_id is None:
             details = loan_id
             # Extract from details dict (assuming structure from LienDTO or similar)
             loan_id_val = details.get('loan_id')
             lienholder_id_val = details.get('lienholder_id')
             principal_val = details.get('principal_remaining')
        else:
             loan_id_val = loan_id
             lienholder_id_val = lienholder_id
             principal_val = principal

        # Ensure loan_id is treated as string for consistency
        loan_id_str = str(loan_id_val)

        unit = next((u for u in self.real_estate_units if u.id == property_id), None)
        if not unit:
             return None

        # Compare as strings to prevent int/str mismatch issues
        if any(str(l['loan_id']) == loan_id_str for l in unit.liens):
             return f"lien_{loan_id_str}"

        lien_id = f"lien_{loan_id_str}"
        new_lien: LienDTO = {
            "loan_id": loan_id_str,
            "lienholder_id": int(lienholder_id_val) if lienholder_id_val is not None else -1,
            "principal_remaining": int(principal_val) if principal_val is not None else 0,
            "lien_type": "MORTGAGE"
        }
        unit.liens.append(new_lien)
        return lien_id

    def remove_lien(self, property_id: int, lien_id: str) -> bool:
        unit = next((u for u in self.real_estate_units if u.id == property_id), None)
        if not unit:
             return False

        original_len = len(unit.liens)
        unit.liens = [l for l in unit.liens if f"lien_{l['loan_id']}" != lien_id and l['loan_id'] != lien_id]

        return len(unit.liens) < original_len

    def transfer_ownership(self, property_id: int, new_owner_id: int) -> bool:
        unit = next((u for u in self.real_estate_units if u.id == property_id), None)
        if not unit:
             return False
        unit.owner_id = new_owner_id
        return True

    def process_transaction(self, tx: "Transaction", state: "SimulationState") -> None:
        tx_type = tx.transaction_type
        item_id = tx.item_id

        if item_id.startswith("real_estate_"):
             self._handle_real_estate_registry(tx, state)
        elif tx_type == "housing" or item_id.startswith("unit_"):
             self._handle_housing_registry(tx, state)
        else:
             self.logger.warning(f"HOUSING_SERVICE | Unknown transaction format: {tx_type}, {item_id}")

    def _handle_real_estate_registry(self, tx: "Transaction", state: "SimulationState"):
        buyer_id = tx.buyer_id
        seller_id = tx.seller_id

        try:
            # real_estate_{id}
            unit_id = int(tx.item_id.split("_")[2])
            unit = next((u for u in self.real_estate_units if u.id == unit_id), None)

            # Resolve agents from state.agents dictionary
            buyer = state.agents.get(buyer_id)
            seller = state.agents.get(seller_id)

            if unit and buyer:
                unit.owner_id = buyer.id

                if seller:
                     if isinstance(seller, IPropertyOwner):
                          seller.remove_property(unit_id)
                     elif hasattr(seller, "owned_properties") and unit_id in seller.owned_properties:
                          seller.owned_properties.remove(unit_id)

                if isinstance(buyer, IPropertyOwner):
                     buyer.add_property(unit_id)
                elif hasattr(buyer, "owned_properties"):
                     buyer.owned_properties.append(unit_id)

                self.logger.info(f"RE_TX | Unit {unit_id} transferred from {seller_id} to {buyer.id}")

        except (IndexError, ValueError) as e:
            self.logger.error(f"RE_TX_FAIL | Invalid item_id format: {tx.item_id}. Error: {e}")

    def _handle_housing_registry(self, tx: "Transaction", state: "SimulationState"):
        buyer = state.agents.get(tx.buyer_id)
        seller = state.agents.get(tx.seller_id)

        try:
            # item_id format: "unit_{id}"
            unit_id = int(tx.item_id.split("_")[1])
            unit = next((u for u in self.real_estate_units if u.id == unit_id), None)

            if not unit:
                self.logger.warning(f"HOUSING_REGISTRY | Unit {unit_id} not found.")
                return

            # Update Unit
            unit.owner_id = tx.buyer_id
            # Update Liens - Remove old mortgages if any (assuming refinancing or fresh purchase clears old mortgage)
            # Logic from Registry:
            unit.liens = [lien for lien in unit.liens if lien['lien_type'] != 'MORTGAGE']

            if tx.metadata and "mortgage_id" in tx.metadata and tx.metadata["mortgage_id"]:
                loan_id = str(tx.metadata["mortgage_id"])
                loan_principal = float(tx.metadata.get("loan_principal", 0.0))
                lender_id = int(tx.metadata.get("lender_id", 0))

                new_lien: LienDTO = {
                    "loan_id": loan_id,
                    "lienholder_id": lender_id,
                    "principal_remaining": loan_principal,
                    "lien_type": "MORTGAGE"
                }
                unit.liens.append(new_lien)

            # Update Seller (if not None/Govt)
            if seller:
                if isinstance(seller, IPropertyOwner):
                    seller.remove_property(unit_id)
                elif hasattr(seller, "owned_properties"):
                    if unit_id in seller.owned_properties:
                        seller.owned_properties.remove(unit_id)

            # Update Buyer
            if buyer:
                if isinstance(buyer, IPropertyOwner):
                    buyer.add_property(unit_id)
                elif hasattr(buyer, "owned_properties"):
                    if unit_id not in buyer.owned_properties:
                        buyer.owned_properties.append(unit_id)

                # Housing System Logic: Auto-move-in if homeless
                if isinstance(buyer, IResident):
                    if buyer.residing_property_id is None:
                        unit.occupant_id = buyer.id
                        buyer.residing_property_id = unit_id
                        buyer.is_homeless = False
                elif hasattr(buyer, "residing_property_id"):
                     if getattr(buyer, "residing_property_id", None) is None:
                        unit.occupant_id = buyer.id
                        buyer.residing_property_id = unit_id
                        buyer.is_homeless = False

            self.logger.info(f"HOUSING_REGISTRY | Unit {unit_id} transferred from {tx.seller_id} to {tx.buyer_id}")

        except (IndexError, ValueError) as e:
            self.logger.error(f"HOUSING_REGISTRY_FAIL | Invalid item_id format: {tx.item_id}. Error: {e}")
