from __future__ import annotations
from typing import TYPE_CHECKING
from modules.common.protocols.api import DTOMapperProtocol, PublicHouseholdDTO
from modules.system.api import DEFAULT_CURRENCY

if TYPE_CHECKING:
    from simulation.core_agents import Household

class HouseholdMapper(DTOMapperProtocol[PublicHouseholdDTO, 'Household']):
    """
    Standard mapper for Household -> PublicHouseholdDTO.
    Isolates External DTO from Kernel internal state.
    """
    
    def to_external(self, kernel_obj: Household) -> PublicHouseholdDTO:
        # Extract safe primitives from the Kernel object
        return PublicHouseholdDTO(
            household_id=str(kernel_obj.id),
            wealth=float(kernel_obj.get_sensory_snapshot().get("total_wealth", 0.0))
        )
        
    def to_kernel(self, external_dto: PublicHouseholdDTO) -> Household:
        # Bidirectional mapping is often restricted for security
        raise NotImplementedError("Converting Public DTO to Kernel Household is not permitted.")
