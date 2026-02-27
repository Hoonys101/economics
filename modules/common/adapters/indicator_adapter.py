from __future__ import annotations
from typing import TYPE_CHECKING
from modules.common.protocols.api import DTOMapperProtocol, PublicEconomicIndicatorsDTO

if TYPE_CHECKING:
    from modules.simulation.api import EconomicIndicatorsDTO

class EconomicIndicatorsMapper(DTOMapperProtocol[PublicEconomicIndicatorsDTO, 'EconomicIndicatorsDTO']):
    """
    Mapper for EconomicIndicatorsDTO -> PublicEconomicIndicatorsDTO.
    Ensures that analysis modules use the Public DTO layer.
    """
    
    def to_external(self, kernel_obj: EconomicIndicatorsDTO) -> PublicEconomicIndicatorsDTO:
        return PublicEconomicIndicatorsDTO(
            gdp=kernel_obj.gdp,
            cpi=kernel_obj.cpi,
            unemployment_rate=kernel_obj.unemployment_rate
        )
        
    def to_kernel(self, external_dto: PublicEconomicIndicatorsDTO) -> EconomicIndicatorsDTO:
        raise NotImplementedError("Converting Public DTO to Kernel Indicators is not permitted.")
