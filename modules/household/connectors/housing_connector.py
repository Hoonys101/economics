from __future__ import annotations
from typing import Any, Protocol, runtime_checkable, Dict
import logging
from modules.household.api import HousingActionDTO

logger = logging.getLogger(__name__)

@runtime_checkable
class IHousingSystem(Protocol):
    def initiate_purchase(self, decision: Dict[str, Any], buyer_id: int) -> None: ...

class HousingConnector:
    """
    Connects Household Agent to the Housing System.
    Abstracts the details of system interaction.
    """
    def execute_action(self, action: HousingActionDTO, housing_system: Any, buyer_id: int) -> None:
        """
        Executes a housing action by calling the appropriate method on the housing system.
        Moved from Household._execute_housing_action.
        """
        if not housing_system:
            return

        if action.action_type == "INITIATE_PURCHASE":
            if isinstance(housing_system, IHousingSystem):
                # Convert to dict expected by legacy HousingSystem
                decision_dict = {
                    "decision_type": "INITIATE_PURCHASE",
                    "target_property_id": int(action.property_id),
                    "offer_price": int(action.offer_price),
                    "down_payment_amount": int(action.down_payment_amount)
                }
                housing_system.initiate_purchase(decision_dict, buyer_id=buyer_id)
                logger.info(f"HOUSING_CONNECTOR | Initiated purchase for property {action.property_id} by agent {buyer_id}")
            else:
                # Fallback for legacy mocks or systems that don't explicitly inherit but have the method (Duck Typing Check via Protocol)
                # Since IHousingSystem is runtime_checkable, isinstance checks structural compatibility.
                # However, if it fails, we log warning.
                # Wait, if `isinstance` works for structural typing, then we are good.
                logger.warning(f"HOUSING_CONNECTOR | Housing system does not support 'initiate_purchase' (Protocol Mismatch).")
        else:
            logger.debug(f"HOUSING_CONNECTOR | Unhandled housing action type: {action.action_type}")
