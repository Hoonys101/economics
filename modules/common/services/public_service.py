from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List, Dict
from modules.common.protocols.api import (
    FirmServiceProtocol, HouseholdServiceProtocol, 
    PublicFirmDTO, PublicHouseholdDTO, PublicEconomicIndicatorsDTO
)
from modules.common.adapters.firm_adapter import FirmMapper
from modules.common.adapters.household_adapter import HouseholdMapper
from modules.common.adapters.indicator_adapter import EconomicIndicatorsMapper
from modules.common.api import (
    IPublicSimulationService, ISimulationRepository, IEventBroker,
    IndicatorSubscriptionDTO, IFirm, IHousehold,
    ProtocolViolationError, AgentNotFoundError, InvalidIndicatorError
)

if TYPE_CHECKING:
    from modules.simulation.api import ISimulationState

class PublicSimulationService(FirmServiceProtocol, HouseholdServiceProtocol, IPublicSimulationService):
    """
    Implementation of the Public API Layer.
    Acts as a facade over the Kernel Simulation, performing DTO mapping.
    """
    
    def __init__(self, repository: ISimulationRepository, event_broker: Optional[IEventBroker] = None):
        self._repository = repository
        self._event_broker = event_broker
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

        # 2. Retrieve from repository
        agent = self._repository.get_agent(int_id)
        if not agent:
             raise AgentNotFoundError(f"Firm not found: {firm_id}")
        
        # 3. Verify type (safe check using Protocol)
        if not isinstance(agent, IFirm):
            raise ProtocolViolationError(f"Agent {firm_id} does not satisfy IFirm protocol")
            
        # 4. Map and return
        return self._firm_mapper.to_external(agent)

    def get_household_status(self, household_id: str) -> PublicHouseholdDTO:
        from modules.simulation.api import AgentID
        try:
            int_id = AgentID(int(household_id))
        except ValueError:
            raise ValueError(f"Invalid household_id format: {household_id}")

        agent = self._repository.get_agent(int_id)
        if not agent:
             raise AgentNotFoundError(f"Household not found: {household_id}")

        if not isinstance(agent, IHousehold):
            raise ProtocolViolationError(f"Agent {household_id} does not satisfy IHousehold protocol")

        return self._household_mapper.to_external(agent)

    def get_global_indicators(self) -> PublicEconomicIndicatorsDTO:
        # Assuming repository or simulation state has this method
        # But ISimulationRepository doesn't strictly have get_economic_indicators in my definition.
        # I need to check if I need to cast repository or update protocol.
        # For now, let's assume repository is the entry point or we inject simulation state separately?
        # The prompt says "Inject ISimulationRepository into the service constructor."
        # And "Refactor methods to use repository".
        # But get_global_indicators relied on self._simulation.
        # Let's assume the repository has access or we keep _simulation if it implements repository?
        # No, strict decoupling means we should rely on repository.
        # Let's check ISimulationRepository definition in common/api.py again.
        # It only has get_agent, get_all_firms...
        # So I might need to update ISimulationRepository or handle indicators differently.
        # The spec says "Fetch entities via repository".
        # It doesn't explicitly mention get_global_indicators refactoring, but "Remove all concrete imports".
        # I will keep get_global_indicators as is but try to use repository if possible, or cast/check.
        # If repository is ISimulationState (which is likely in main), it works.
        # But for strictness, I should probably add get_economic_indicators to ISimulationRepository or inject IWorldStateMetricsProvider.
        # Given the task scope, I will assume the repository passed in *is* the simulation state or has the method.
        # But to be safe with strict typing, I will check hasattr or casting.

        # Wait, the prompt says "Inject ISimulationRepository".
        # If I can't use _simulation, how do I get indicators?
        # I will optimistically try to get it from repository if available, or raise NotImplementedError if strict repo doesn't support it.
        # Actually, legacy code used self._simulation.
        # I will assume the repository implements IWorldStateMetricsProvider or similar if provided.
        # For now, I'll access it if available.
        if hasattr(self._repository, 'get_economic_indicators'):
            kernel_indicators = self._repository.get_economic_indicators()
            return self._indicator_mapper.to_external(kernel_indicators)
        else:
            # Fallback or strict error?
            # I'll raise NotImplementedError as the repo doesn't support it yet
            raise NotImplementedError("Repository does not support get_economic_indicators")

    def process_transaction(self, firm_id: str, amount: float) -> bool:
        # This would delegate to a kernel transaction processor
        # Implementation depends on the concrete finance system
        raise NotImplementedError("Transaction processing via Public API is not yet implemented.")

    # --- IPublicSimulationService Implementation ---

    def subscribe_to_indicators(self, request: IndicatorSubscriptionDTO) -> bool:
        if not self._event_broker:
            # If no broker is injected, we cannot subscribe.
            # Or we can return False / Log warning.
            return False

        # Delegate to broker
        # We assume the broker knows how to handle "economic_indicators" topic or similar.
        # Or we map keys to topics.
        # For this implementation, I will subscribe to a generic "indicators" topic
        # and the callback will filter? Or specific topics?
        # The spec says "register callbacks in an injected stateless event bus".
        # I'll implement a simple delegation.
        self._event_broker.subscribe("economic_indicators", lambda data: self._handle_indicator_update(request, data))
        return True

    def query_indicators(self, keys: List[str]) -> Dict[str, float]:
        # This requires pulling data.
        # If repository supports it, great.
        # I'll reuse get_global_indicators logic or fail.
        if hasattr(self._repository, 'get_economic_indicators'):
             # This gets a DTO. I need to map keys to DTO fields.
             indicators = self._repository.get_economic_indicators()
             result = {}
             for key in keys:
                 if hasattr(indicators, key):
                     result[key] = getattr(indicators, key)
                 else:
                     raise InvalidIndicatorError(f"Indicator {key} not found")
             return result
        raise NotImplementedError("Repository does not support query_indicators")

    def _handle_indicator_update(self, subscription: IndicatorSubscriptionDTO, data: Dict[str, float]) -> None:
        # Filter data based on subscription keys
        filtered = {k: v for k, v in data.items() if k in subscription.indicator_keys}
        if filtered:
            subscription.callback(filtered)
