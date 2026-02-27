from __future__ import annotations
from typing import TYPE_CHECKING, Any
from modules.common.protocols.api import DTOMapperProtocol, PublicFirmDTO
from modules.common.api import ProtocolViolationError

if TYPE_CHECKING:
    from simulation.firms import Firm

class FirmMapper(DTOMapperProtocol[PublicFirmDTO, 'Firm']):
    """
    Standard mapper for Firm -> PublicFirmDTO.
    Isolates External DTO from Kernel internal state.
    """
    
    def to_external(self, kernel_obj: Any) -> PublicFirmDTO:
        # Hard Firewall: Explicitly validate required attributes
        required_attrs = ['id', 'capital_stock', 'get_all_items']
        for attr in required_attrs:
            if not hasattr(kernel_obj, attr):
                raise ProtocolViolationError(f"Firm Protocol Violation: Missing attribute '{attr}' in {type(kernel_obj).__name__}")

        # Extract safe primitives from the Kernel object
        try:
            inventory = kernel_obj.get_all_items()
            inventory_count = sum(inventory.values()) if inventory else 0

            return PublicFirmDTO(
                firm_id=str(kernel_obj.id),
                capital=float(kernel_obj.capital_stock),
                inventory_count=int(inventory_count)
            )
        except (ValueError, TypeError, AttributeError) as e:
             raise ProtocolViolationError(f"Firm Mapping Error: {e}")
        
    def to_kernel(self, external_dto: PublicFirmDTO) -> Firm:
        # Bidirectional mapping is often restricted for security
        raise NotImplementedError("Converting Public DTO to Kernel Firm is not permitted.")
