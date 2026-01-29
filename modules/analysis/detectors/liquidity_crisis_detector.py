from typing import List, Dict, Any
from modules.analysis.api import IDetector, PhenomenonEventDTO, DetectorConfigDTO
from modules.simulation.api import ISimulationState

class LiquidityCrisisDetector(IDetector):
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

        thresholds = self.config.get('thresholds', {})
        min_reserve_ratio = thresholds.get('bank_reserve_ratio_min', 0.05)

        if not self.sys_state:
            return events

        reserves = self.sys_state['bank_total_reserves']
        deposits = self.sys_state['bank_total_deposits']

        if deposits > 0:
            ratio = reserves / deposits
            if ratio < min_reserve_ratio:
                severity = 1.0 - (ratio / min_reserve_ratio) if min_reserve_ratio > 0 else 1.0
                events.append({
                    'detector_name': 'LiquidityCrisisDetector',
                    'start_tick': self.current_tick,
                    'end_tick': self.current_tick,
                    'severity': max(0.0, min(1.0, severity)),
                    'message': f"Bank reserve ratio critical: {ratio:.2%}",
                    'details': {'reserves': reserves, 'deposits': deposits, 'ratio': ratio}
                })

        return events
