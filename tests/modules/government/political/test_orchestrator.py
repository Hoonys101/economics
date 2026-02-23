import pytest
from modules.government.political.orchestrator import PoliticalOrchestrator
from modules.government.political.api import VoteRecordDTO, LobbyingEffortDTO

class TestPoliticalOrchestrator:

    @pytest.fixture
    def orchestrator(self):
        return PoliticalOrchestrator()

    def test_vote_aggregation(self, orchestrator):
        # Inject votes
        # 90 Agents vote Approval (1.0) with weight 1
        for i in range(90):
            orchestrator.register_vote(VoteRecordDTO(
                agent_id=i, tick=1, approval_value=1.0, primary_grievance="NONE", political_weight=1.0
            ))

        # 10 Agents vote Disapproval (0.0) with weight 50
        for i in range(90, 100):
            orchestrator.register_vote(VoteRecordDTO(
                agent_id=i, tick=1, approval_value=0.0, primary_grievance="HIGH_TAX", political_weight=50.0
            ))

        climate = orchestrator.calculate_political_climate(1)

        # Calculation:
        # Total Weight = 90*1 + 10*50 = 90 + 500 = 590
        # Weighted Approval Sum = (90 * 1.0 * 1) + (10 * 0.0 * 50) = 90
        # Approval = 90 / 590 = 0.15254...

        assert 0.15 < climate.overall_approval_rating < 0.16
        assert "HIGH_TAX" in climate.top_grievances

    def test_lobbying_pressure(self, orchestrator):
        # Inject Lobbying
        # Firm A: Lower Tax (-0.05), Investment 50000
        orchestrator.register_lobbying(LobbyingEffortDTO(
            firm_id=1, tick=1, target_policy="CORPORATE_TAX", desired_shift=-0.05, investment_pennies=50000
        ))

        # Firm B: Raise Tax (+0.05), Investment 10000
        orchestrator.register_lobbying(LobbyingEffortDTO(
            firm_id=2, tick=1, target_policy="CORPORATE_TAX", desired_shift=0.05, investment_pennies=10000
        ))

        climate = orchestrator.calculate_political_climate(1)

        # Net Pressure: (50000 * -0.05) + (10000 * 0.05) = -2500 + 500 = -2000
        assert climate.lobbying_pressure["CORPORATE_TAX"] == -2000.0

    def test_reset_cycle(self, orchestrator):
        orchestrator.register_vote(VoteRecordDTO(1, 1, 1.0, "NONE", 1.0))
        orchestrator.reset_cycle()
        climate = orchestrator.calculate_political_climate(2)
        assert climate.overall_approval_rating == 0.5 # Default when no votes
