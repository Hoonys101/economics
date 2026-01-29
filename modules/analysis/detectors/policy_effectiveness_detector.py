from typing import List
from modules.analysis.api import IDetector, PhenomenonEventDTO, DetectorConfigDTO
from modules.simulation.api import ISimulationState

class PolicyEffectivenessDetector(IDetector):
    def __init__(self, config: DetectorConfigDTO):
        self.config = config
        self.current_tick = 0
        self.sim_state = None
        self.sys_state = None

    def update(self, tick: int, sim_state: ISimulationState) -> None:
        self.current_tick = tick
        self.sim_state = sim_state
        self.sys_state = sim_state.get_system_state()

    def analyze(self) -> List[PhenomenonEventDTO]:
        events = []
        if not self.config.get('enabled', False):
            return events

        if not self.sys_state or not self.sim_state:
            return events

        # 1. Fiscal Policy Activation
        last_fiscal_tick = self.sys_state.get('fiscal_policy_last_activation_tick', -1)
        if last_fiscal_tick == self.current_tick:
             events.append({
                'detector_name': 'PolicyEffectivenessDetector',
                'start_tick': self.current_tick,
                'end_tick': self.current_tick,
                'severity': 0.5, # Informational
                'message': "Fiscal Stimulus Activated",
                'details': {'type': 'fiscal_stimulus'}
            })

        # 2. Monetary Policy ZLB
        base_rate = self.sys_state.get('central_bank_base_rate', 0.05)
        zlb_threshold = 0.001
        if base_rate < zlb_threshold:
             events.append({
                'detector_name': 'PolicyEffectivenessDetector',
                'start_tick': self.current_tick,
                'end_tick': self.current_tick,
                'severity': 0.8,
                'message': f"Zero Lower Bound Hit: {base_rate:.4f}",
                'details': {'type': 'zlb', 'rate': base_rate}
            })

        return events
