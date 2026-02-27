from __future__ import annotations
from typing import TYPE_CHECKING
from modules.common.protocols.api import DTOMapperProtocol, PublicFirmDTO

if TYPE_CHECKING:
    from simulation.firms import Firm

class FirmMapper(DTOMapperProtocol[PublicFirmDTO, 'Firm']):
    """
    Standard mapper for Firm -> PublicFirmDTO.
    Isolates External DTO from Kernel internal state.
    """
    
    def to_external(self, kernel_obj: Firm) -> PublicFirmDTO:
        # Extract safe primitives from the Kernel object
        return PublicFirmDTO(
            firm_id=str(kernel_obj.id),
            capital=float(kernel_obj.capital_stock),
            inventory_count=int(sum(kernel_obj.get_all_items().values()))
        )
        
    def to_kernel(self, external_dto: PublicFirmDTO) -> Firm:
        # Bidirectional mapping is often restricted for security
        raise NotImplementedError("Converting Public DTO to Kernel Firm is not permitted.")
