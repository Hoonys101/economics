import unittest
import threading
from modules.system.server_bridge import TelemetryExchange
from simulation.dtos.telemetry import TelemetrySnapshotDTO
from modules.system.api import MarketSnapshotDTO
import time

class TestTelemetryExchange(unittest.TestCase):
    def test_update_notifies_listener(self):
        te = TelemetryExchange()
        notified = False

        def callback():
            nonlocal notified
            notified = True

        te.subscribe(callback)
        data = TelemetrySnapshotDTO(timestamp=time.time(), tick=1, data={"key": "value"}, errors=[], metadata={})
        te.update(data)

        self.assertTrue(notified)
        self.assertEqual(te.get(), data)

    def test_unsubscribe_stops_notification(self):
        te = TelemetryExchange()
        count = 0

        def callback():
            nonlocal count
            count += 1

        te.subscribe(callback)
        data1 = TelemetrySnapshotDTO(timestamp=time.time(), tick=1, data={"k": "v1"}, errors=[], metadata={})
        te.update(data1)
        self.assertEqual(count, 1)

        te.unsubscribe(callback)
        data2 = TelemetrySnapshotDTO(timestamp=time.time(), tick=2, data={"k": "v2"}, errors=[], metadata={})
        te.update(data2)
        self.assertEqual(count, 1) # Should not increment
        self.assertEqual(te.get(), data2)

    def test_thread_safety(self):
        te = TelemetryExchange()
        errors = []

        def listener():
            # Simulate slow listener
            import time
            time.sleep(0.001)

        te.subscribe(listener)

        def updater():
            for i in range(100):
                try:
                    data = TelemetrySnapshotDTO(timestamp=time.time(), tick=i, data={}, errors=[], metadata={})
                    te.update(data)
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=updater) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")

if __name__ == '__main__':
    unittest.main()
