import logging
import logging.config
import json
import os
import random


class TsvFormatter(logging.Formatter):
    """Tab-separated values formatter for logging."""

    def format(self, record):
        # Manually order the fields
        ordered_info = {
            "timestamp": record.created,
            "tick": getattr(record, "tick", -1),
            "agent_type": getattr(record, "agent_type", "System"),
            "agent_id": getattr(record, "agent_id", -1),
            "method_name": getattr(record, "method_name", "Unknown"),
            "message": record.getMessage(),
            "extra": json.dumps(getattr(record, "extra", {})),
        }
        return "\t".join(map(str, ordered_info.values()))


class CsvFormatter(logging.Formatter):
    """CSV formatter for logging."""

    def __init__(self, fmt=None, datefmt=None, style="%", fieldnames=None):
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)
        self.fieldnames = (
            fieldnames
            if fieldnames is not None
            else [
                "timestamp",
                "tick",
                "agent_type",
                "agent_id",
                "method_name",
                "message",
                "extra",
            ]
        )

    def format(self, record):
        # Create a dictionary for the record
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "tick": getattr(record, "tick", -1),
            "agent_type": getattr(record, "agent_type", "System"),
            "agent_id": getattr(record, "agent_id", -1),
            "method_name": getattr(record, "method_name", "Unknown"),
            "message": record.getMessage().replace('"', '""'),  # Escape quotes
            "extra": json.dumps(getattr(record, "extra", {})),
        }

        # Use csv to format the record
        import csv
        import io

        output = io.StringIO()
        writer = csv.DictWriter(
            output, fieldnames=self.fieldnames, quoting=csv.QUOTE_ALL
        )

        # This is a bit of a hack to write a single row without the header
        # writer.writeheader() # Don't write header for every log line
        writer.writerow(log_record)
        return output.getvalue().strip()


class SamplingFilter(logging.Filter):
    """
    A logging filter that applies sampling rates to log records based on their method_name.
    """

    def __init__(self, name=""):
        super().__init__(name)
        self.sampling_rates = {}

    def filter(self, record):
        method_name = getattr(record, "method_name", "Unknown")
        rate = self.sampling_rates.get(method_name, 1.0)
        if random.random() > rate:
            return False
        return True


def setup_logging(
    default_path="log_config.json", default_level=logging.INFO, env_key="LOG_CFG"
):
    """Setup logging configuration from a JSON file."""
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, "rt") as f:
            config_dict = json.load(f)

        # Ensure log directory exists if specified in config
        for handler_name, handler_config in config_dict.get("handlers", {}).items():
            if "filename" in handler_config:
                log_dir = os.path.dirname(handler_config["filename"])
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir)

        logging.config.dictConfig(config_dict)
        logging.info("Logging setup complete from config file.")
    else:
    else:
        # Standardize fallback logging format
        logging.basicConfig(
            level=default_level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        logging.info(
            "Logging setup complete with basic configuration (config file not found). Standard format applied."
        )

    # Write header to CSV file if a CSV handler is configured
    # This part needs to be dynamic based on the loaded config
    # For now, assuming a 'file' handler with CsvFormatter and a specific filename
    log_dir = "logs"
    log_file_path = os.path.join(log_dir, "simulation_log_StandardLog.csv")
    if (
        os.path.exists(log_file_path) and os.path.getsize(log_file_path) == 0
    ):  # Only write header if file is empty
        with open(log_file_path, "w", newline="") as f:
            import csv

            writer = csv.writer(f)
            writer.writerow(
                [
                    "timestamp",
                    "tick",
                    "agent_type",
                    "agent_id",
                    "method_name",
                    "message",
                    "extra",
                ]
            )
