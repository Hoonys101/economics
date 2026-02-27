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
    IPublicSimulationService, ISimulationRepository, IEventBroker, IMetricsProvider,
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
    
    def __init__(
        self,
        repository: ISimulationRepository,
        metrics_provider: Optional[IMetricsProvider] = None,
        event_broker: Optional[IEventBroker] = None
    ):
        self._repository = repository
        self._metrics_provider = metrics_provider
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
        if not self._metrics_provider:
             raise NotImplementedError("Metrics Provider is not available")

        kernel_indicators = self._metrics_provider.get_economic_indicators()
        return self._indicator_mapper.to_external(kernel_indicators)

    def process_transaction(self, firm_id: str, amount: float) -> bool:
        # This would delegate to a kernel transaction processor
        # Implementation depends on the concrete finance system
        raise NotImplementedError("Transaction processing via Public API is not yet implemented.")

    # --- IPublicSimulationService Implementation ---

    def subscribe_to_indicators(self, request: IndicatorSubscriptionDTO) -> bool:
        if not self._event_broker:
            # If no broker is injected, we cannot subscribe.
            return False

        # Delegate to broker
        self._event_broker.subscribe("economic_indicators", lambda data: self._handle_indicator_update(request, data))
        return True

    def query_indicators(self, keys: List[str]) -> Dict[str, float]:
        if not self._metrics_provider:
             raise NotImplementedError("Metrics Provider is not available")

        # This gets a DTO. Map keys to DTO fields using explicit mapping or safe retrieval.
        indicators = self._metrics_provider.get_economic_indicators()

        # Safe Mapping Logic (DTO to Dict)
        # Assuming indicators is a dataclass or object with attributes
        # We try to convert to dict safely
        data_map = {}
        if hasattr(indicators, '__dict__'):
            data_map = vars(indicators)
        elif hasattr(indicators, '_asdict'): # NamedTuple
            data_map = indicators._asdict()
        else:
            # Fallback manual extraction or error
            raise NotImplementedError("Cannot serialize indicators DTO")

        result = {}
        for key in keys:
             if key in data_map:
                 result[key] = data_map[key]
             else:
                 raise InvalidIndicatorError(f"Indicator {key} not found")
        return result

    def _handle_indicator_update(self, subscription: IndicatorSubscriptionDTO, data: Dict[str, float]) -> None:
        # Filter data based on subscription keys
        filtered = {k: v for k, v in data.items() if k in subscription.indicator_keys}
        if filtered:
            subscription.callback(filtered)
