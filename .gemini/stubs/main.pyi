from _typeshed import Incomplete
from modules.common.utils.logging_manager import SamplingFilter

main_logger: Incomplete
sampling_filter: SamplingFilter | None
sampling_filter = filter_obj

def run_simulation(firm_production_targets=None, initial_firm_inventory_mean=None, output_filename: str = 'simulation_results.csv') -> None: ...
