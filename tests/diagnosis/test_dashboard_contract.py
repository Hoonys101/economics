
import pytest
from unittest.mock import MagicMock, patch
from app import app
from simulation.dtos import DashboardSnapshotDTO, DashboardGlobalIndicatorsDTO, SocietyTabDataDTO

@pytest.fixture
def mock_sim_instance():
    sim = MagicMock()
    sim.time = 42
    sim.run_id = 1
    return sim

def test_dashboard_snapshot_endpoint_structure():
    """Phase 3-A: /api/simulation/dashboard 엔드포인트의 DTO 구조 및 필드 정합성 검증"""
    with app.app_context():
        with patch('app.SnapshotViewModel') as MockVM:
            mock_vm_instance = MockVM.return_value
            
            # Setup Mock Response according to DashboardSnapshotDTO
            global_indicators = DashboardGlobalIndicatorsDTO(
                death_rate=0.1,
                bankruptcy_rate=0.2,
                employment_rate=95.0,
                gdp=1000.0,
                avg_wage=50.0,
                gini=0.35,
                avg_tax_rate=0.25,
                avg_leisure_hours=8.0,
                parenting_rate=10.0
            )
            
            society_tab = SocietyTabDataDTO(
                generations=[],
                mitosis_cost=100.0,
                unemployment_pie={"struggling": 5, "voluntary": 10},
                time_allocation={"work": 40.0, "parenting": 10.0},
                avg_leisure_hours=8.0
            )
            
            snapshot = DashboardSnapshotDTO(
                tick=42,
                global_indicators=global_indicators,
                tabs={"society": society_tab, "government": {}, "market": {}, "finance": {}}
            )
            
            mock_vm_instance.get_dashboard_snapshot.return_value = snapshot

            with patch('app.get_or_create_simulation') as mock_get_sim:
                mock_sim = MagicMock()
                mock_sim.time = 42
                mock_get_sim.return_value = mock_sim
                
                with patch('app.get_repository'):
                    # Act
                    client = app.test_client()
                    response = client.get('/api/simulation/dashboard')
                    
                    # Assert
                    assert response.status_code == 200
                    data = response.get_json()
                    
                    assert data["tick"] == 42
                    assert "global_indicators" in data
                    assert data["global_indicators"]["avg_tax_rate"] == 0.25
                    assert data["global_indicators"]["avg_leisure_hours"] == 8.0
                    
                    assert "tabs" in data
                    assert "society" in data["tabs"]
                    assert data["tabs"]["society"]["time_allocation"]["parenting"] == 10.0
                    assert "government" in data["tabs"]
