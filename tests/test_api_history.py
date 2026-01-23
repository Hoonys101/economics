import unittest
import json
import logging
import app as app_module


class TestHistoryAPI(unittest.TestCase):
    def setUp(self):
        self.app = app_module.app.test_client()
        self.app.testing = True

        # Initialize a fresh simulation
        with app_module.app.app_context():
            app_module.create_simulation()
            # Suppress logging for cleaner test output
            logging.getLogger("app").setLevel(logging.WARNING)

    def test_gdp_history_on_refresh(self):
        """
        Verify that fetching update with since=0 returns the full history of GDP.
        """
        print("\n--- Running History API Verification ---")

        # Access the global simulation instance dynamically
        sim = app_module.simulation_instance
        if sim is None:
            self.fail("Simulation instance is None after creation")

        # 1. Run 5 ticks
        with app_module.simulation_lock:
            for i in range(5):
                sim.run_tick()
                print(f"Ran tick {sim.time}")

        # 2. Call the update endpoint with since=0
        response = self.app.get("/api/simulation/update?since=0")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)

        # 3. Analyze the response
        gdp_history = data.get("chart_update", {}).get("new_gdp_history", [])
        current_tick = data.get("tick")

        print(f"Current Tick: {current_tick}")
        print(f"Received GDP History Length: {len(gdp_history)}")
        print(f"GDP History Data: {gdp_history}")

        # 4. Assertions
        # We expect at least 5 data points
        self.assertGreaterEqual(
            len(gdp_history),
            5,
            f"Expected at least 5 GDP data points, but got {len(gdp_history)}",
        )

        # Check if values are numeric
        for val in gdp_history:
            self.assertIsInstance(val, (int, float))


if __name__ == "__main__":
    unittest.main()
