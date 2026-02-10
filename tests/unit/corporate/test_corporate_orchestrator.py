import pytest
from unittest.mock import MagicMock
from dataclasses import replace
from simulation.decisions.corporate_manager import CorporateManager
from simulation.schemas import FirmActionVector

def test_orchestration(firm_dto, context_mock):
    config = MagicMock()
    manager = CorporateManager(config)

    vector = FirmActionVector(
        rd_aggressiveness=1.0,
        capital_aggressiveness=0.0,
        dividend_aggressiveness=1.0,
        debt_aggressiveness=0.0,
        hiring_aggressiveness=0.5,
        sales_aggressiveness=0.5
    )

    # Mock System 2 planner to avoid heavy logic
    manager.system2_planner = MagicMock()
    manager.system2_planner.project_future.return_value = {}

    # Setup state for HR and Sales to produce orders
    # Use replace for frozen DTO
    new_prod = replace(firm_dto.production,
        production_target=200.0,
        inventory={"food": 100.0}
    )
    new_hr = replace(firm_dto.hr, employees=[])

    new_fin = replace(firm_dto.finance, balance=10000.0, revenue_this_turn=1000.0)

    firm_dto = replace(firm_dto, production=new_prod, hr=new_hr, finance=new_fin)
    context_mock.state = firm_dto

    orders = manager.realize_ceo_actions(firm_dto, context_mock, vector)

    # Check if orders from different departments are present
    types = set(o.order_type for o in orders)

    # Finance (Dividend)
    assert "SET_DIVIDEND" in types

    # HR (Hiring)
    # Check logic: target 200, inventory 100 -> gap 100. Need labor.
    # Should produce BUY labor orders.
    assert "BUY" in types

    # Operations (RD)
    assert "INVEST_RD" in types

    # Sales (Sell)
    assert "SELL" in types
