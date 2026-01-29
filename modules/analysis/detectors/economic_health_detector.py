from typing import List, Deque
from collections import deque
from modules.analysis.api import IDetector, PhenomenonEventDTO, DetectorConfigDTO
from modules.simulation.api import ISimulationState

class EconomicHealthDetector(IDetector):
    def __init__(self, config: DetectorConfigDTO):
        self.config = config
        self.current_tick = 0
        self.sim_state = None
        self.cpi_history: Deque[float] = deque(maxlen=2) # Current and previous

    def update(self, tick: int, sim_state: ISimulationState) -> None:
        self.current_tick = tick
        self.sim_state = sim_state

        snapshot = sim_state.get_market_snapshot()
        cpi = snapshot.get('cpi', 0.0)
        self.cpi_history.append(cpi)

    def analyze(self) -> List[PhenomenonEventDTO]:
        events = []
        if not self.config.get('enabled', False):
            return events

        if not self.sim_state:
            return events

        thresholds = self.config.get('thresholds', {})

        inflation_upper = thresholds.get('inflation_upper_bound', 0.05)
        inflation_lower = thresholds.get('inflation_lower_bound', -0.01)

        inflation = 0.0
        if len(self.cpi_history) >= 2:
            prev_cpi = self.cpi_history[0]
            curr_cpi = self.cpi_history[1]
            if prev_cpi > 0:
                inflation = (curr_cpi - prev_cpi) / prev_cpi

        if inflation > inflation_upper:
            events.append({
                'detector_name': 'EconomicHealthDetector',
                'start_tick': self.current_tick,
                'end_tick': self.current_tick,
                'severity': min(1.0, (inflation - inflation_upper) * 10),
                'message': f"High Inflation: {inflation:.2%}",
                'details': {'type': 'inflation', 'value': inflation}
            })
        elif inflation < inflation_lower:
             events.append({
                'detector_name': 'EconomicHealthDetector',
                'start_tick': self.current_tick,
                'end_tick': self.current_tick,
                'severity': min(1.0, (inflation_lower - inflation) * 10),
                'message': f"Deflation/Low Inflation: {inflation:.2%}",
                'details': {'type': 'inflation', 'value': inflation}
            })

        return events
