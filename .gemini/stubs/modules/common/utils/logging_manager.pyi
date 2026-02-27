import logging
from _typeshed import Incomplete

class TsvFormatter(logging.Formatter):
    """Tab-separated values formatter for logging."""
    def format(self, record): ...

class CsvFormatter(logging.Formatter):
    """CSV formatter for logging."""
    fieldnames: Incomplete
    def __init__(self, fmt=None, datefmt=None, style: str = '%', fieldnames=None) -> None: ...
    def format(self, record): ...

class SamplingFilter(logging.Filter):
    """
    A logging filter that applies sampling rates to log records based on their method_name.
    """
    sampling_rates: Incomplete
    def __init__(self, name: str = '') -> None: ...
    def filter(self, record): ...

def setup_logging(default_path: str = 'log_config.json', default_level=..., env_key: str = 'LOG_CFG') -> None:
    """Setup logging configuration from a JSON file."""
