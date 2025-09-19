import csv
import datetime
import os
import random
import logging
import json
from typing import List, Optional

class CustomFormatter(logging.Formatter):
    def format(self, record):
        # Ensure 'tick' and 'agent_id' are present in the record for formatting
        if not hasattr(record, 'tick'):
            record.tick = 'N/A'
        if not hasattr(record, 'agent_id'):
            record.agent_id = 'N/A'
        if not hasattr(record, 'tags'):
            record.tags = []
        return super().format(record)

class ContextualFilter(logging.Filter):
    """
    log_config.json의 필터 규칙에 따라 로그 레코드를 필터링하는 클래스.
    """
    def __init__(self, filters):
        super().__init__()
        self.filters = filters

    def filter(self, record):
        # Module filter
        modules = self.filters.get('modules')
        if modules and record.name not in modules:
            return False
                
        return True

class Logger:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self, log_dir="logs"):
        if Logger._initialized:
            return

        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.files = {}
        self.writers = {}
        self.headers = {}
        
        self.allowed_log_types: Optional[List[str]] = None

        self.root_logger = logging.getLogger()
        self._reconfigure_handlers() # Configure standard logging here

        self.log_levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        self._min_log_level = logging.DEBUG # This is for CSV logging, not standard logging

        self._sampling_rates = {}
        self._special_log_methods = []

        Logger._initialized = True

    def _reconfigure_handlers(self):
        """Safely removes all existing handlers and re-adds them based on log_config.json."""
        for handler in self.root_logger.handlers[:]:
            try:
                handler.close()
            except Exception:
                pass
            self.root_logger.removeHandler(handler)

        # Read log_config.json
        config_path = 'log_config.json'
        log_config = {}
        if os.path.exists(config_path):
            with open(config_path, 'rt') as f:
                log_config = json.load(f)

        if not log_config.get('enabled', False):
            logging.disable(logging.CRITICAL)
            return

        log_level = log_config.get('level', 'INFO').upper()
        self.root_logger.setLevel(log_level)

        output = log_config.get('output', 'console')
        if output == 'file':
            log_file = log_config.get('log_file', 'logs/debug_custom.log')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            handler = logging.FileHandler(log_file, mode='w')
        else:
            handler = logging.StreamHandler()

        formatter = CustomFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - (Tick: %(tick)s, Agent: %(agent_id)s) - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        if 'filters' in log_config:
            context_filter = ContextualFilter(log_config['filters'])
            handler.addFilter(context_filter)

        self.root_logger.addHandler(handler)
        self.root_logger.info("Logging system configured successfully by custom Logger.")

    def _get_writer(self, log_type, header):
        if log_type not in self.writers:
            log_file_path = os.path.join(self.log_dir, f"simulation_log_{log_type}.csv")
            file_exists = os.path.exists(log_file_path)
            file = open(log_file_path, 'a', newline='', encoding='utf-8')
            writer = csv.writer(file)
            
            self.files[log_type] = file
            self.writers[log_type] = writer
            self.headers[log_type] = header

            if not file_exists or os.stat(log_file_path).st_size == 0:
                writer.writerow(header)
        return self.writers[log_type]

    def _write_log(self, level, log_type, tick, agent_type, agent_id, method_name, message, **kwargs):
        # Filtering logic based on the allowed list
        if self.allowed_log_types is not None and log_type not in self.allowed_log_types:
            return

        # This _min_log_level is for CSV logging, standard logging is handled by root_logger's level
        if level < self._min_log_level:
            return

        if method_name not in self._special_log_methods:
            sampling_rate = self._sampling_rates.get(method_name, 1.0)
            if random.random() > sampling_rate:
                return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare data for CSV
        if log_type == "EconomicIndicatorTracker":
            full_header = sorted(kwargs.keys())
            row_data = [kwargs[key] for key in full_header]
        else:
            base_header = ['timestamp', 'tick', 'agent_type', 'agent_id', 'method_name', 'message']
            dynamic_header_keys = sorted(kwargs.keys())
            full_header = base_header + dynamic_header_keys
            row_data = [timestamp, tick, agent_type, agent_id, method_name, message]
            for key in dynamic_header_keys:
                row_data.append(kwargs.get(key, ''))

        writer = self._get_writer(log_type, full_header)
        writer.writerow(row_data)
        self.files[log_type].flush()

        # Also send to standard logger for console/debug_custom.log output
        log_message_for_std_logger = f"[{log_type}] Tick: {tick}, Agent: {agent_type}-{agent_id}, Method: {method_name}, Msg: {message}"
        if kwargs:
            log_message_for_std_logger += f", Data: {kwargs}"
        
        # Pass extra attributes for CustomFormatter and ContextualFilter
        extra_for_std_logger = {
            'tick': tick,
            'agent_id': agent_id,
            'tags': kwargs.get('tags', []) # Pass tags if available
        }
        self.root_logger.log(level, log_message_for_std_logger, extra=extra_for_std_logger)


    def log(self, level, message, log_type='StandardLog', tick=-1, agent_type='System', agent_id=-1, method_name='Unknown', **kwargs):
        # This method is now the primary entry point for all logging.
        # It will handle both CSV logging and forwarding to the standard Python logger.
        
        # Prepare kwargs for CSV logging
        csv_kwargs = kwargs.copy()
        
        # Call _write_log for CSV logging
        self._write_log(level, log_type, tick, agent_type, agent_id, method_name, message, **csv_kwargs)

    def debug(self, message, log_type='StandardLog', tick=-1, agent_type='System', agent_id=-1, method_name='Unknown', **kwargs):
        self.log(logging.DEBUG, message, log_type, tick, agent_type, agent_id, method_name, **kwargs)

    def info(self, message, log_type='StandardLog', tick=-1, agent_type='System', agent_id=-1, method_name='Unknown', **kwargs):
        self.log(logging.INFO, message, log_type, tick, agent_type, agent_id, method_name, **kwargs)

    def warning(self, message, log_type='StandardLog', tick=-1, agent_type='System', agent_id=-1, method_name='Unknown', **kwargs):
        self.log(logging.WARNING, message, log_type, tick, agent_type, agent_id, method_name, **kwargs)

    def error(self, message, log_type='StandardLog', tick=-1, agent_type='System', agent_id=-1, method_name='Unknown', **kwargs):
        self.log(logging.ERROR, message, log_type, tick, agent_type, agent_id, method_name, **kwargs)

    def critical(self, message, log_type='StandardLog', tick=-1, agent_type='System', agent_id=-1, method_name='Unknown', **kwargs):
        self.log(logging.CRITICAL, message, log_type, tick, agent_type, agent_id, method_name, **kwargs)

    def set_allowed_log_types(self, allowed_types: Optional[List[str]]):
        """
        Sets the list of allowed log_types. If set, only these types will be logged to CSV.
        :param allowed_types: A list of strings representing the log_types to allow, or None to allow all.
        """
        self.allowed_log_types = allowed_types
        self.info(f"Log types allowed for CSV: {allowed_types}", log_type="LoggerConfig", method_name="set_allowed_log_types")

    def set_min_log_level(self, level):
        if level not in self.log_levels.values():
            raise ValueError(f"Invalid log level: {level}. Use logging.DEBUG, INFO, WARNING, ERROR, CRITICAL.")
        self._min_log_level = level
        self.info(f"Minimum log level for CSV set to: {logging.getLevelName(level)}", log_type="LoggerConfig", method_name="set_min_log_level")

    def set_sampling_rate(self, method_name, rate):
        if not (0.0 <= rate <= 1.0):
            raise ValueError("Sampling rate must be between 0.0 and 1.0.")
        self._sampling_rates[method_name] = rate
        self.info(f"Sampling rate for method '{method_name}' set to: {rate}", log_type="LoggerConfig", method_name="set_sampling_rate")

    def clear_logs(self):
        self.close()
        for filename in os.listdir(self.log_dir):
            if filename.startswith("simulation_log_") and filename.endswith(".csv"):
                os.remove(os.path.join(self.log_dir, filename))
        self.files = {}
        self.writers = {}
        self.headers = {}
        self.root_logger.info("All simulation CSV logs cleared.")

    def close(self):
        for file_handle in self.files.values():
            file_handle.close()
        self.files = {}
        self.writers = {}
        self.headers = {}
        # Do not remove handlers from root_logger here, as it's managed by _reconfigure_handlers
        # and might be used by other parts of the application.
        Logger._initialized = False
        self.root_logger.info("Custom Logger instance closed.")

    def save_to_file(self, filename="simulation_results.csv"):
        # This method seems to be a placeholder or for a different purpose.
        # The CSV logging is handled automatically by _write_log.
        pass

    def __getstate__(self):
        state = self.__dict__.copy()
        if '_instance' in state:
            del state['_instance']
        del state['files']
        del state['writers']
        del state['headers']
        del state['root_logger'] 
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.files = {}
        self.writers = {}
        self.headers = {}
        
        self.root_logger = logging.getLogger()
        self._reconfigure_handlers()
        
        Logger._initialized = True