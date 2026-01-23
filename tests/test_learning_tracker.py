import unittest
from simulation.ai.learning_tracker import LearningTracker


class TestLearningTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = LearningTracker()

    def test_get_summary_no_data(self):
        """Test summary generation when no data has been tracked."""
        summary = self.tracker.get_summary()
        self.assertEqual(summary["total_ticks_tracked"], 0)
        self.assertIn("message", summary)

    def test_get_summary_single_agent(self):
        """Test summary with one agent and multiple records."""
        self.tracker.track_learning_progress(
            tick=1, agent_id="agent_1", q_table_change=0.1, reward=10
        )
        self.tracker.track_learning_progress(
            tick=2, agent_id="agent_1", q_table_change=0.05, reward=5
        )

        summary = self.tracker.get_summary()

        self.assertEqual(summary["total_ticks_tracked"], 2)

        # Overall stats
        overall = summary["overall"]
        self.assertEqual(overall["record_count"], 2)
        self.assertAlmostEqual(overall["total_q_table_change"], 0.15)
        self.assertAlmostEqual(overall["average_q_table_change"], 0.075)
        self.assertAlmostEqual(overall["total_reward"], 15)
        self.assertAlmostEqual(overall["average_reward"], 7.5)

        # Per-agent stats
        per_agent = summary["per_agent"]
        self.assertIn("agent_1", per_agent)
        agent_1_stats = per_agent["agent_1"]
        self.assertEqual(agent_1_stats["record_count"], 2)
        self.assertAlmostEqual(agent_1_stats["total_q_change"], 0.15)
        self.assertAlmostEqual(agent_1_stats["avg_q_change"], 0.075)
        self.assertAlmostEqual(agent_1_stats["total_reward"], 15)
        self.assertAlmostEqual(agent_1_stats["avg_reward"], 7.5)

    def test_get_summary_multiple_agents(self):
        """Test summary with multiple agents across multiple ticks."""
        # Tick 1
        self.tracker.track_learning_progress(
            tick=1, agent_id="agent_1", q_table_change=0.1, reward=10
        )
        self.tracker.track_learning_progress(
            tick=1, agent_id="agent_2", q_table_change=0.2, reward=20
        )

        # Tick 2
        self.tracker.track_learning_progress(
            tick=2, agent_id="agent_1", q_table_change=0.05, reward=5
        )
        self.tracker.track_learning_progress(
            tick=2, agent_id="agent_2", q_table_change=0.15, reward=15
        )

        summary = self.tracker.get_summary()

        self.assertEqual(summary["total_ticks_tracked"], 2)

        # Overall stats
        overall = summary["overall"]
        self.assertEqual(overall["record_count"], 4)
        self.assertAlmostEqual(overall["total_q_table_change"], 0.1 + 0.2 + 0.05 + 0.15)
        self.assertAlmostEqual(
            overall["average_q_table_change"], (0.1 + 0.2 + 0.05 + 0.15) / 4
        )
        self.assertAlmostEqual(overall["total_reward"], 10 + 20 + 5 + 15)
        self.assertAlmostEqual(overall["average_reward"], (10 + 20 + 5 + 15) / 4)

        # Per-agent stats for agent_2
        agent_2_stats = summary["per_agent"]["agent_2"]
        self.assertEqual(agent_2_stats["record_count"], 2)
        self.assertAlmostEqual(agent_2_stats["total_q_change"], 0.2 + 0.15)
        self.assertAlmostEqual(agent_2_stats["avg_q_change"], (0.2 + 0.15) / 2)
        self.assertAlmostEqual(agent_2_stats["total_reward"], 20 + 15)
        self.assertAlmostEqual(agent_2_stats["avg_reward"], (20 + 15) / 2)


if __name__ == "__main__":
    unittest.main()
