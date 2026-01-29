from typing import List, Dict, Any, Type
import importlib
import re
from collections import defaultdict
from modules.analysis.api import (
    IAnalyzer, IDetector, AnalysisConfigDTO, PhenomenaReportDTO,
    PhenomenonEventDTO, ResilienceIndexDTO, PolicySynergyMetrics
)
from modules.simulation.api import ISimulationState

class PhenomenaAnalyzer(IAnalyzer):
    def __init__(self, config: AnalysisConfigDTO):
        self.config = config
        self.detectors: List[IDetector] = []
        self.history: Dict[str, List[float]] = defaultdict(list)
        self.simulation_ticks = 0
        self._load_detectors()

    def _load_detectors(self):
        detector_configs = self.config.get('detectors', {})
        for name, det_conf in detector_configs.items():
            if not det_conf.get('enabled', False):
                continue

            module_path_str = det_conf['module']
            try:
                # Dynamic import logic
                # Expecting 'package.subpackage.ClassName'
                # Convert ClassName to snake_case module name

                parts = module_path_str.split('.')
                class_name = parts[-1]
                package_path = ".".join(parts[:-1])

                # Convert CamelCase to snake_case
                module_name = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()

                full_module_name = f"{package_path}.{module_name}"

                module = importlib.import_module(full_module_name)
                detector_class = getattr(module, class_name)

                detector_instance = detector_class(det_conf)
                self.detectors.append(detector_instance)

            except (ImportError, AttributeError, ValueError) as e:
                # Fallback: Try importing directly if the user provided the module path instead of class path
                # or if the file structure doesn't match snake_case convention exactly.
                try:
                    # Try assuming the last part is the module, and we need to find the class?
                    # Or maybe the path provided IS the module path, and we guess the class?
                    # Spec says: 'modules.analysis.detectors.LiquidityCrisisDetector'
                    # My implementation handles this specific case.
                    print(f"Failed to load detector {name} with inferred path {full_module_name}: {e}")
                except Exception:
                    pass

    def run_tick(self, tick: int, sim_state: ISimulationState) -> None:
        self.simulation_ticks = max(self.simulation_ticks, tick)
        for detector in self.detectors:
            detector.update(tick, sim_state)

        # Record time series
        snapshot = sim_state.get_market_snapshot()
        self.history['gdp'].append(snapshot.get('gdp', 0.0))
        self.history['cpi'].append(snapshot.get('cpi', 0.0))

    def generate_report(self) -> PhenomenaReportDTO:
        all_events = []
        for detector in self.detectors:
            all_events.extend(detector.analyze())

        resilience_index = self._calculate_resilience(all_events)
        policy_metrics = self._calculate_policy_synergy(all_events)

        return {
            'simulation_ticks': self.simulation_ticks,
            'resilience_index': resilience_index,
            'policy_metrics': policy_metrics,
            'detected_events': all_events,
            'key_timeseries': dict(self.history)
        }

    def _calculate_resilience(self, events: List[PhenomenonEventDTO]) -> ResilienceIndexDTO:
        weights = self.config.get('resilience_weights', {})
        base_score = 100.0

        crisis_penalty = 0.0
        severity_weight = weights.get('crisis_severity_weight', 0.3)

        for event in events:
            severity = event.get('severity', 0.0)
            # Simple scoring model
            crisis_penalty += severity * severity_weight * 5.0

        final_score = max(0.0, base_score - crisis_penalty)

        return {
            'final_score': final_score,
            'volatility_score': 0.0, # Placeholder
            'recovery_score': 0.0,   # Placeholder
            'crisis_penalty': crisis_penalty,
            'policy_bonus': 0.0      # Placeholder
        }

    def _calculate_policy_synergy(self, events: List[PhenomenonEventDTO]) -> PolicySynergyMetrics:
        fiscal_count = sum(1 for e in events if e['detector_name'] == 'PolicyEffectivenessDetector' and 'Fiscal' in e['message'])
        monetary_count = sum(1 for e in events if e['detector_name'] == 'PolicyEffectivenessDetector' and 'Zero Lower Bound' in e['message'])

        return {
            'fiscal_stabilizer_activations': fiscal_count,
            'monetary_stabilizer_activations': monetary_count,
            'correlation_gdp_fiscal_stimulus': 0.0,
            'zlb_duration': monetary_count
        }
