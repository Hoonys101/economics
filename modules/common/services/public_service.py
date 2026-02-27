from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List
from modules.common.protocols.api import (
    FirmServiceProtocol, HouseholdServiceProtocol, 
    PublicFirmDTO, PublicHouseholdDTO, PublicEconomicIndicatorsDTO
)
from modules.common.adapters.firm_adapter import FirmMapper
from modules.common.adapters.household_adapter import HouseholdMapper
from modules.common.adapters.indicator_adapter import EconomicIndicatorsMapper

if TYPE_CHECKING:
    from modules.simulation.api import ISimulationState

class PublicSimulationService(FirmServiceProtocol, HouseholdServiceProtocol):
    """
    Implementation of the Public API Layer.
    Acts as a facade over the Kernel Simulation, performing DTO mapping.
    """
    
    def __init__(self, kernel_simulation: ISimulationState):
        self._simulation = kernel_simulation
        self._firm_mapper = FirmMapper()
        self._household_mapper = HouseholdMapper()
        self._indicator_mapper = EconomicIndicatorsMapper()

    def get_firm_status(self, firm_id: str) -> PublicFirmDTO:
        # 1. Convert string ID to internal AgentID
        from modules.simulation.api import AgentID
        try:
            int_id = AgentID(int(firm_id))
        except ValueError:
            raise ValueError(f"Invalid firm_id format: {firm_id}")

        # 2. Retrieve from kernel
        agent = self._simulation.agents.get(int_id)
        if not agent:
             raise KeyError(f"Firm not found: {firm_id}")
        
        # 3. Verify type (safe check)
        from simulation.firms import Firm
        if not isinstance(agent, Firm):
            raise TypeError(f"Agent {firm_id} is not a Firm")
            
        # 4. Map and return
        return self._firm_mapper.to_external(agent)

    def get_household_status(self, household_id: str) -> PublicHouseholdDTO:
        from modules.simulation.api import AgentID
        try:
            int_id = AgentID(int(household_id))
        except ValueError:
            raise ValueError(f"Invalid household_id format: {household_id}")

        agent = self._simulation.agents.get(int_id)
        if not agent:
             raise KeyError(f"Household not found: {household_id}")

        from simulation.core_agents import Household
        if not isinstance(agent, Household):
            raise TypeError(f"Agent {household_id} is not a Household")

        return self._household_mapper.to_external(agent)

    def get_global_indicators(self) -> PublicEconomicIndicatorsDTO:
        kernel_indicators = self._simulation.get_economic_indicators()
        return self._indicator_mapper.to_external(kernel_indicators)

    def process_transaction(self, firm_id: str, amount: float) -> bool:
        # This would delegate to a kernel transaction processor
        # Implementation depends on the concrete finance system
        raise NotImplementedError("Transaction processing via Public API is not yet implemented.")
