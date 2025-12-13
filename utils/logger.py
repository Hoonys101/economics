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
        if not hasattr(record, "tick"):
            record.tick = "N/A"
        if not hasattr(record, "agent_id"):
            record.agent_id = "N/A"
        if not hasattr(record, "tags"):
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
        modules = self.filters.get("modules")
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
        self._reconfigure_handlers()  # Configure standard logging here

        self.log_levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        self._min_log_level = (
            logging.DEBUG
        )  # This is for CSV logging, not standard logging

        self._sampling_rates = {}
        self._special_log_methods = []
        self._agent_sampling_pool: Optional[List[int]] = (
            None  # New attribute for dynamic sampling
        )

        # Log rotation settings
        self._max_log_file_size_bytes: int = 10 * 1024 * 1024  # Default 10 MB
        self._max_log_files: int = 5  # Default 5 files

        Logger._initialized = True

    def clear_logs(self):
        """
        Closes all open log files and deletes them.
        """
        for log_type, file in self.files.items():
            file.close()
        self.files = {}
        self.writers = {}
        self.headers = {}

        for file_name in os.listdir(self.log_dir):
            if file_name.startswith("simulation_log_") and file_name.endswith(".csv"):
                try:
                    os.remove(os.path.join(self.log_dir, file_name))
                except OSError as e:
                    self.error(
                        f"Error removing log file {file_name}: {e}",
                        log_type="LoggerConfig",
                        method_name="clear_logs",
                    )

    def _reconfigure_handlers(self):
        """Safely removes all existing handlers and re-adds them based on log_config.json."""
        for handler in self.root_logger.handlers[:]:
            try:
                handler.close()
            except Exception:
                pass
            self.root_logger.removeHandler(handler)

        # Read log_config.json
        config_path = "log_config.json"
        log_config = {}
        if os.path.exists(config_path):
            with open(config_path, "rt") as f:
                log_config = json.load(f)

        if not log_config.get("enabled", False):
            logging.disable(logging.CRITICAL)
            return

        log_level = log_config.get("level", "INFO").upper()
        self.root_logger.setLevel(log_level)

        output = log_config.get("output", "console")
        if output == "file":
            log_file = log_config.get("log_file", "logs/debug_custom.log")
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            handler = logging.FileHandler(log_file, mode="w")
        else:
            handler = logging.StreamHandler()

        formatter = CustomFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - (Tick: %(tick)s, Agent: %(agent_id)s) - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        if "filters" in log_config:
            context_filter = ContextualFilter(log_config["filters"])
            handler.addFilter(context_filter)

        self.root_logger.addHandler(handler)
        self.root_logger.info(
            "Logging system configured successfully by custom Logger."
        )

        # Update log rotation settings from config
        rotation_config = log_config.get("rotation", {})
        self._max_log_file_size_bytes = (
            rotation_config.get("max_file_size_mb", 10) * 1024 * 1024
        )
        self._max_log_files = rotation_config.get("max_files", 5)

    def _get_writer(self, log_type, header):
        log_file_path = os.path.join(self.log_dir, f"simulation_log_{log_type}.csv")

        # Check for log rotation before returning writer
        if log_type in self.files and os.path.exists(log_file_path):
            if os.path.getsize(log_file_path) >= self._max_log_file_size_bytes:
                self._rotate_log_file(log_type)

        if log_type not in self.writers:
            file_exists = os.path.exists(log_file_path)
            file = open(log_file_path, "a", newline="", encoding="utf-8")
            writer = csv.writer(file)

            self.files[log_type] = file
            self.writers[log_type] = writer
            self.headers[log_type] = header

            if not file_exists or os.stat(log_file_path).st_size == 0:
                writer.writerow(header)
        return self.writers[log_type]

    def _rotate_log_file(self, log_type: str):
        """
        Rotates the log file for a given log_type.
        Closes the current file, renames it, and opens a new one.
        """
        if log_type in self.files:
            self.files[log_type].close()
            del self.files[log_type]
            del self.writers[log_type]

        base_path = os.path.join(self.log_dir, f"simulation_log_{log_type}.csv")

        # Shift existing log files
        for i in range(self._max_log_files - 1, 0, -1):
            src = f"{base_path}.{i - 1}"
            dst = f"{base_path}.{i}"
            if os.path.exists(src):
                if os.path.exists(dst):
                    os.remove(dst)
                os.rename(src, dst)

        # Rename current log file to .0
        if os.path.exists(base_path):
            if os.path.exists(f"{base_path}.0"):
                os.remove(f"{base_path}.0")
            os.rename(base_path, f"{base_path}.0")

        self.info(
            f"Log file for {log_type} rotated.",
            log_type="LoggerConfig",
            method_name="_rotate_log_file",
        )

    def _write_log(
        self,
        level,
        log_type,
        tick,
        agent_type,
        agent_id,
        method_name,
        message,
        is_conditional=False,
        threshold_met=False,
        is_event=False,
        **kwargs,
    ):
        # Filtering logic based on the allowed list
        if (
            self.allowed_log_types is not None
            and log_type not in self.allowed_log_types
        ):
            return

        # This _min_log_level is for CSV logging, standard logging is handled by root_logger's level
        if level < self._min_log_level:
            return

        # Conditional Logging: Skip if conditional and threshold not met
        if is_conditional and not threshold_met:
            return

        # Dynamic Sampling for agents: Only log if agent_id is in the sampling pool, unless it's an event
        if (
            not is_event
            and agent_id != -1
            and self._agent_sampling_pool is not None
            and agent_id not in self._agent_sampling_pool
        ):
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
            base_header = [
                "timestamp",
                "tick",
                "agent_type",
                "agent_id",
                "method_name",
                "message",
            ]
            dynamic_header_keys = sorted(kwargs.keys())
            full_header = base_header + dynamic_header_keys
            row_data = [timestamp, tick, agent_type, agent_id, method_name, message]
            for key in dynamic_header_keys:
                row_data.append(kwargs.get(key, ""))

        writer = self._get_writer(log_type, full_header)
        writer.writerow(row_data)
        self.files[log_type].flush()

        # Also send to standard logger for console/debug_custom.log output
        log_message_for_std_logger = f"[{log_type}] Tick: {tick}, Agent: {agent_type}-{agent_id}, Method: {method_name}, Msg: {message}"
        if kwargs:
            log_message_for_std_logger += f", Data: {kwargs}"

        # Pass extra attributes for CustomFormatter and ContextualFilter
        extra_for_std_logger = {
            "tick": tick,
            "agent_id": agent_id,
            "tags": kwargs.get("tags", []),  # Pass tags if available
        }
        self.root_logger.log(
            level, log_message_for_std_logger, extra=extra_for_std_logger
        )

    def set_agent_sampling_pool(self, agent_ids: Optional[List[int]]):
        """
        Sets the list of agent IDs for which detailed logs should be recorded.
        If set to None, all agents will be logged (subject to other filters).
        :param agent_ids: A list of agent IDs to sample, or None to disable agent sampling.
        """
        self._agent_sampling_pool = agent_ids
        self.info(
            f"Agent sampling pool set to: {agent_ids}",
            log_type="LoggerConfig",
            method_name="set_agent_sampling_pool",
        )

    def set_sampling_rate(self, method_name: str, rate: float):
        """
        Sets the sampling rate for a specific method_name.
        :param method_name: The name of the method to apply sampling to.
        :param rate: The sampling rate (0.0 to 1.0). 0.0 means no logs, 1.0 means all logs.
        """
        if not 0.0 <= rate <= 1.0:
            raise ValueError("Sampling rate must be between 0.0 and 1.0")
        self._sampling_rates[method_name] = rate
        self.info(
            f"Sampling rate for {method_name} set to {rate}",
            log_type="LoggerConfig",
            method_name="set_sampling_rate",
        )

    def log(
        self,
        level,
        message,
        log_type="StandardLog",
        tick=-1,
        agent_type="System",
        agent_id=-1,
        method_name="Unknown",
        is_conditional=False,
        threshold_met=False,
        is_event=False,
        **kwargs,
    ):
        # This method is now the primary entry point for all logging.
        # It will handle both CSV logging and forwarding to the standard Python logger.

        # Check if the log level is sufficient for CSV logging
        if level < self._min_log_level:
            return

        # Prepare kwargs for CSV logging
        csv_kwargs = kwargs.copy()

        # Call _write_log for CSV logging
        self._write_log(
            level,
            log_type,
            tick,
            agent_type,
            agent_id,
            method_name,
            message,
            is_conditional=is_conditional,
            threshold_met=threshold_met,
            is_event=is_event,
            **csv_kwargs,
        )

    def set_log_level(self, level_name: str):
        """
        Sets the minimum log level for both CSV logging and the standard Python logger.
        :param level_name: Name of the log level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        """
        level = self.log_levels.get(level_name.upper())
        if level is None:
            raise ValueError(
                f"Invalid log level name: {level_name}. Use DEBUG, INFO, WARNING, ERROR, CRITICAL."
            )

        self._min_log_level = level
        self.root_logger.setLevel(level)  # Update standard logger level
        self.info(
            f"Global log level set to: {level_name.upper()}",
            log_type="LoggerConfig",
            method_name="set_log_level",
        )
        # Reconfigure handlers to apply the new level, especially for file handlers that might be created later
        self._reconfigure_handlers()

    def debug(
        self,
        message,
        log_type="StandardLog",
        tick=-1,
        agent_type="System",
        agent_id=-1,
        method_name="Unknown",
        is_conditional=False,
        threshold_met=False,
        is_event=False,
        **kwargs,
    ):
        self.log(
            logging.DEBUG,
            message,
            log_type,
            tick,
            agent_type,
            agent_id,
            method_name,
            is_conditional,
            threshold_met,
            is_event,
            **kwargs,
        )

    def info(
        self,
        message,
        log_type="StandardLog",
        tick=-1,
        agent_type="System",
        agent_id=-1,
        method_name="Unknown",
        is_conditional=False,
        threshold_met=False,
        is_event=False,
        **kwargs,
    ):
        self.log(
            logging.INFO,
            message,
            log_type,
            tick,
            agent_type,
            agent_id,
            method_name,
            is_conditional,
            threshold_met,
            is_event,
            **kwargs,
        )

    def warning(
        self,
        message,
        log_type="StandardLog",
        tick=-1,
        agent_type="System",
        agent_id=-1,
        method_name="Unknown",
        is_conditional=False,
        threshold_met=False,
        is_event=False,
        **kwargs,
    ):
        self.log(
            logging.WARNING,
            message,
            log_type,
            tick,
            agent_type,
            agent_id,
            method_name,
            is_conditional,
            threshold_met,
            is_event,
            **kwargs,
        )

    def error(
        self,
        message,
        log_type="StandardLog",
        tick=-1,
        agent_type="System",
        agent_id=-1,
        method_name="Unknown",
        is_conditional=False,
        threshold_met=False,
        is_event=False,
        **kwargs,
    ):
        self.log(
            logging.ERROR,
            message,
            log_type,
            tick,
            agent_type,
            agent_id,
            method_name,
            is_conditional,
            threshold_met,
            is_event,
            **kwargs,
        )

    def critical(
        self,
        message,
        log_type="StandardLog",
        tick=-1,
        agent_type="System",
        agent_id=-1,
        method_name="Unknown",
        is_conditional=False,
        threshold_met=False,
        is_event=False,
        **kwargs,
    ):
        self.log(
            logging.CRITICAL,
            message,
            log_type,
            tick,
            agent_type,
            agent_id,
            method_name,
            is_conditional,
            threshold_met,
            is_event,
            **kwargs,
        )
