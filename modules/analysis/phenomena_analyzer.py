from typing import List, Dict, Any, Type
import importlib
import re
import math
import statistics
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

            # SECURITY CHECK: Prevent RCE by enforcing whitelist
            if not module_path_str.startswith("modules.analysis.detectors."):
                raise ValueError(f"Security violation: Detector {name} uses unsafe module path '{module_path_str}'. Must start with 'modules.analysis.detectors.'")

            # Dynamic import logic
            # Expecting 'package.subpackage.ClassName'
            parts = module_path_str.split('.')
            class_name = parts[-1]
            package_path = ".".join(parts[:-1])

            # Convert CamelCase to snake_case for file import
            module_name = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()

            full_module_name = f"{package_path}.{module_name}"

            try:
                module = importlib.import_module(full_module_name)
                detector_class = getattr(module, class_name)

                detector_instance = detector_class(det_conf)
                self.detectors.append(detector_instance)

            except (ImportError, AttributeError) as e:
                # TD-154: Fail fast on configuration errors instead of silent failure
                raise ValueError(f"Failed to load detector {name} from {full_module_name}: {e}") from e


    def run_tick(self, tick: int, sim_state: ISimulationState) -> None:
        self.simulation_ticks = max(self.simulation_ticks, tick)
        for detector in self.detectors:
            detector.update(tick, sim_state)

        # Record time series
        indicators = sim_state.get_economic_indicators()
        self.history['gdp'].append(indicators.gdp)
        self.history['cpi'].append(indicators.cpi)

    def generate_report(self) -> PhenomenaReportDTO:
        all_events = []
        for detector in self.detectors:
            all_events.extend(detector.analyze())

        policy_metrics = self._calculate_policy_synergy(all_events)
        resilience_index = self._calculate_resilience(all_events, policy_metrics)

        return {
            'simulation_ticks': self.simulation_ticks,
            'resilience_index': resilience_index,
            'policy_metrics': policy_metrics,
            'detected_events': all_events,
            'key_timeseries': dict(self.history)
        }

    def _calculate_resilience(self, events: List[PhenomenonEventDTO], policy_metrics: PolicySynergyMetrics) -> ResilienceIndexDTO:
        weights = self.config.get('resilience_weights', {})
        base_score = 100.0

        # 1. Crisis Penalty
        crisis_penalty = 0.0
        severity_weight = weights.get('crisis_severity_weight', 0.3)
        for event in events:
            severity = event.get('severity', 0.0)
            crisis_penalty += severity * severity_weight * 5.0

        # 2. Volatility Score (Stability)
        volatility_score = 0.0
        if len(self.history['gdp']) > 2:
            try:
                # Calculate Coefficient of Variation (CV) = Stdev / Mean
                gdp_data = self.history['gdp']
                mean_gdp = statistics.mean(gdp_data)
                stdev_gdp = statistics.stdev(gdp_data)

                if mean_gdp > 0:
                    cv = stdev_gdp / mean_gdp
                    # Map CV to score: 0 CV -> 100 score, >0.1 CV -> 0 score
                    volatility_score = max(0.0, 100.0 * (1.0 - (cv * 10.0)))
            except statistics.StatisticsError:
                pass

        # 3. Policy Bonus
        policy_bonus_factor = weights.get('policy_bonus_factor', 1.1)
        total_activations = policy_metrics['fiscal_stabilizer_activations'] + policy_metrics['monetary_stabilizer_activations']
        policy_bonus = total_activations * 2.0 * policy_bonus_factor # 2 points per activation

        # 4. Recovery Score (Placeholder / TODO)
        recovery_score = 0.0

        final_score = max(0.0, min(100.0, base_score - crisis_penalty + policy_bonus + (volatility_score * 0.1)))

        return {
            'final_score': final_score,
            'volatility_score': volatility_score,
            'recovery_score': recovery_score,
            'crisis_penalty': crisis_penalty,
            'policy_bonus': policy_bonus
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
