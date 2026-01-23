from unittest.mock import MagicMock
from typing import Dict, Type, Any, Union, List
import json
import os


class GoldenLoader:
    """
    Utility to load JSON fixtures and convert them to MagicMock objects.
    """

    @staticmethod
    def load_json(path: str) -> Dict[str, Any]:
        """
        Safely loads JSON files from the filesystem.

        Args:
            path: Path to the JSON file.

        Returns:
            Dict containing the loaded JSON data.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Golden fixture not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def dict_to_mock(data: Any, spec: Type = None) -> Any:
        """
        Recursively converts nested dictionaries into nested MagicMock objects.

        Args:
            data: The dictionary or list to convert.
            spec: Optional class to use as the spec for the created Mock (only for the top-level dict).
                  Nested dictionaries will be converted to generic MagicMocks.

        Returns:
            MagicMock object if input is a dict.
            List of objects/Mocks if input is a list.
            Original value if input is a primitive.
        """
        if isinstance(data, dict):
            mock = MagicMock(spec=spec)
            for key, value in data.items():
                # Recursively convert value
                child = GoldenLoader.dict_to_mock(value)
                setattr(mock, key, child)
            return mock
        elif isinstance(data, list):
            return [GoldenLoader.dict_to_mock(item) for item in data]
        else:
            return data
