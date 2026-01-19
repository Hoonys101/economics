import unittest
import os
import json
from unittest.mock import MagicMock
from tests.utils.golden_loader import GoldenLoader

class TestGoldenLoader(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_fixture.json"
        self.data = {
            "name": "Test Agent",
            "attributes": {
                "age": 30,
                "skills": ["coding", "testing"]
            },
            "history": [
                {"year": 2020, "event": "hired"},
                {"year": 2021, "event": "promoted"}
            ]
        }
        with open(self.test_file, 'w') as f:
            json.dump(self.data, f)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_load_json(self):
        loaded = GoldenLoader.load_json(self.test_file)
        self.assertEqual(loaded, self.data)

    def test_load_json_not_found(self):
        with self.assertRaises(FileNotFoundError):
            GoldenLoader.load_json("non_existent_file.json")

    def test_dict_to_mock_basic(self):
        mock = GoldenLoader.dict_to_mock(self.data)
        self.assertIsInstance(mock, MagicMock)
        self.assertEqual(mock.name, "Test Agent")
        self.assertIsInstance(mock.attributes, MagicMock)
        self.assertEqual(mock.attributes.age, 30)
        self.assertEqual(mock.attributes.skills, ["coding", "testing"])

    def test_dict_to_mock_nested_list(self):
        mock = GoldenLoader.dict_to_mock(self.data)
        self.assertIsInstance(mock.history, list)
        self.assertEqual(len(mock.history), 2)
        self.assertIsInstance(mock.history[0], MagicMock)
        self.assertEqual(mock.history[0].year, 2020)
        self.assertEqual(mock.history[1].event, "promoted")

    def test_dict_to_mock_with_spec(self):
        class Agent:
            pass

        mock = GoldenLoader.dict_to_mock(self.data, spec=Agent)
        self.assertIsInstance(mock, MagicMock)
        # Verify spec is set (isinstance checks against the spec class usually work for Mocks with spec)
        self.assertIsInstance(mock, Agent)

        # Check data is still there
        self.assertEqual(mock.name, "Test Agent")

    def test_primitives(self):
        self.assertEqual(GoldenLoader.dict_to_mock(123), 123)
        self.assertEqual(GoldenLoader.dict_to_mock("string"), "string")
        self.assertEqual(GoldenLoader.dict_to_mock(None), None)
