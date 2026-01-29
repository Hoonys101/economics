from typing import List
from modules.analysis.api import IDetector, PhenomenonEventDTO, DetectorConfigDTO
from modules.simulation.api import ISimulationState

class CircuitBreakerDetector(IDetector):
    def __init__(self, config: DetectorConfigDTO):
        self.config = config
        self.current_tick = 0
        self.sys_state = None

    def update(self, tick: int, sim_state: ISimulationState) -> None:
        self.current_tick = tick
        self.sys_state = sim_state.get_system_state()

    def analyze(self) -> List[PhenomenonEventDTO]:
        events = []
        if not self.config.get('enabled', False):
            return events

        if not self.sys_state:
            return events

        if self.sys_state.get('is_circuit_breaker_active', False):
            events.append({
                'detector_name': 'CircuitBreakerDetector',
                'start_tick': self.current_tick,
                'end_tick': self.current_tick,
                'severity': 1.0,
                'message': "Market-wide trading halt triggered.",
                'details': {}
            })

        return events
