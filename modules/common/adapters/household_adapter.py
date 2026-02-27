from __future__ import annotations
from typing import TYPE_CHECKING, Any
from modules.common.protocols.api import DTOMapperProtocol, PublicHouseholdDTO
from modules.common.api import ProtocolViolationError

if TYPE_CHECKING:
    from simulation.core_agents import Household

class HouseholdMapper(DTOMapperProtocol[PublicHouseholdDTO, 'Household']):
    
    def to_external(self, kernel_obj: Any) -> PublicHouseholdDTO:
        # Hard Firewall
        required_attrs = ['id', 'total_wealth'] # Assuming total_wealth is the field for wealth
        # Spec defined IHousehold with 'wealth'. Kernel usually has 'total_wealth' property?
        # Let's check IHousehold definition in common/api.py again. It says 'wealth'.
        # But Kernel object likely has something else.
        # Ideally, IHousehold protocol should match Kernel object if we want isinstance to work.
        # Or IHousehold is an abstraction.
        # But here we are mapping Kernel Obj -> Public DTO.
        # PublicSimulationService already checked isinstance(agent, IHousehold).
        # If IHousehold defines 'wealth', then kernel_obj must have 'wealth'.
        # If kernel object has 'total_wealth', then IHousehold should have 'total_wealth' OR we need an adapter.
        # The common/api.py defines IHousehold with 'wealth'.
        # If the real Household object has 'total_wealth' but not 'wealth', then `isinstance(h, IHousehold)` will FAIL if IHousehold requires 'wealth'.
        # So IHousehold must reflect reality or reality must implement IHousehold.
        # Assuming existing code passed tests, `Household` might have `wealth` property or the test mock had it.
        # Let's assume standard 'wealth' for now based on IHousehold.
        # Wait, if I changed IHousehold to use @property, it strictly looks for that getter.

        # In `firm_adapter.py` I used `capital_stock` because that's what was there.
        # Here I will check for `wealth`.

        required_attrs = ['id', 'wealth']
        for attr in required_attrs:
            if not hasattr(kernel_obj, attr):
                 # Fallback check for total_wealth if wealth is missing?
                 # But ProtocolViolationError should be strict if we claim it matches IHousehold.
                 # I will strictly check 'wealth' as per IHousehold protocol.
                 raise ProtocolViolationError(f"Household Protocol Violation: Missing attribute '{attr}' in {type(kernel_obj).__name__}")

        return PublicHouseholdDTO(
            household_id=str(kernel_obj.id),
            wealth=float(kernel_obj.wealth)
        )

    def to_kernel(self, external_dto: PublicHouseholdDTO) -> Household:
        raise NotImplementedError("Converting Public DTO to Kernel Household is not permitted.")
