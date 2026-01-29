from typing import List
from modules.analysis.api import IDetector, PhenomenonEventDTO, DetectorConfigDTO
from modules.simulation.api import ISimulationState

class SolvencyDetector(IDetector):
    def __init__(self, config: DetectorConfigDTO):
        self.config = config
        self.current_tick = 0
        self.sim_state = None

    def update(self, tick: int, sim_state: ISimulationState) -> None:
        self.current_tick = tick
        self.sim_state = sim_state

    def analyze(self) -> List[PhenomenonEventDTO]:
        events = []
        if not self.config.get('enabled', False):
            return events

        if not self.sim_state:
            return events

        thresholds = self.config.get('thresholds', {})
        bankruptcy_rate_max = thresholds.get('bankruptcy_rate_max', 0.10)

        insolvent_count = 0
        total_agents = 0

        # Check households
        for hh in self.sim_state.households:
             if getattr(hh, 'is_active', False):
                 total_agents += 1
                 assets = getattr(hh, 'assets', 0.0)
                 if assets < 0:
                     insolvent_count += 1

        # Check firms
        for firm in self.sim_state.firms:
             if getattr(firm, 'is_active', False):
                 total_agents += 1
                 assets = getattr(firm, 'assets', 0.0)
                 if assets < 0:
                     insolvent_count += 1

        rate = insolvent_count / total_agents if total_agents > 0 else 0.0

        if rate > bankruptcy_rate_max:
            severity = (rate - bankruptcy_rate_max) / (1.0 - bankruptcy_rate_max) if bankruptcy_rate_max < 1.0 else 1.0
            events.append({
                'detector_name': 'SolvencyDetector',
                'start_tick': self.current_tick,
                'end_tick': self.current_tick,
                'severity': min(1.0, max(0.0, severity)),
                'message': f"Insolvency rate critical: {rate:.2%}",
                'details': {'insolvent_count': insolvent_count, 'total_agents': total_agents, 'rate': rate}
            })

        return events
