from unittest.mock import MagicMock
from typing import Dict, Type, Any, Union, List, Optional
import json
import os
from dataclasses import dataclass, asdict

from modules.household.dtos import HouseholdStateDTO
from simulation.dtos.firm_state_dto import FirmStateDTO
from simulation.ai.api import Personality

class GoldenLoader:
    """
    Utility to load JSON fixtures and convert them to MagicMock objects or DTOs.
    Serves as the central production utility for fixture loading.
    """

    def __init__(self, data: Dict[str, Any]):
        self.metadata = data.get("metadata", {})
        self.households_data = data.get("households", [])
        self.firms_data = data.get("firms", [])
        self.config_snapshot = data.get("config_snapshot", {})

    @staticmethod
    def load_json(path: str) -> Dict[str, Any]:
        """
        Safely loads JSON files from the filesystem.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Golden fixture not found at: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def dict_to_mock(data: Any, spec: Type = None) -> Any:
        """
        Recursively converts nested dictionaries into nested MagicMock objects.
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

    @classmethod
    def load(cls, filepath: str) -> "GoldenLoader":
        """Load a golden fixture from file."""
        data = cls.load_json(filepath)
        return cls(data)

    def create_household_mocks(self, mock_class=None):
        """
        Create mock households from golden data.
        """
        mocks = []
        for h_data in self.households_data:
            from types import SimpleNamespace
            if mock_class:
                mock = MagicMock(spec=mock_class)
            else:
                mock = SimpleNamespace()
            for key, value in h_data.items():
                setattr(mock, key, value)

            # Add default mocks for methods/engines usually expected
            mock.make_decision = MagicMock(return_value=([], MagicMock()))
            if not hasattr(mock, 'decision_engine'):
                mock.decision_engine = MagicMock()
            if not hasattr(mock.decision_engine, 'ai_engine'):
                mock.decision_engine.ai_engine = MagicMock()
            mocks.append(mock)
        return mocks

    def create_household_dto_list(self) -> List[HouseholdStateDTO]:
        """Creates actual HouseholdStateDTO objects from golden data."""
        dtos = []
        for h_data in self.households_data:
            # Map fields safely, providing defaults for missing fields
            dto = HouseholdStateDTO(
                id=h_data.get("id", 0),
                assets=h_data.get("assets", 0.0),
                inventory=h_data.get("inventory", {}),
                needs=h_data.get("needs", {}),
                preference_asset=1.0,
                preference_social=1.0,
                preference_growth=1.0,
                personality=Personality.BALANCED,
                durable_assets=[],
                expected_inflation={},
                is_employed=h_data.get("is_employed", False),
                current_wage=h_data.get("current_wage", 0.0),
                wage_modifier=1.0,
                is_homeless=False,
                residing_property_id=None,
                owned_properties=[],
                portfolio_holdings={},
                risk_aversion=1.0,
                agent_data=h_data, # Use raw dict as agent_data
                perceived_prices={},
                conformity=0.5,
                social_rank=0.5,
                approval_rating=float(h_data.get("approval_rating", 1.0)),
                sentiment_index=float(h_data.get("sentiment_index", 0.5)),
                perceived_fair_price=float(h_data.get("perceived_fair_price", 0.0))
            )
            dtos.append(dto)
        return dtos

    def create_firm_mocks(self, mock_class=None):
        """Create mock firms from golden data."""
        mocks = []
        for f_data in self.firms_data:
            from types import SimpleNamespace
            if mock_class:
                mock = MagicMock(spec=mock_class)
            else:
                mock = SimpleNamespace()
            for key, value in f_data.items():
                setattr(mock, key, value)

            mock.make_decision = MagicMock(return_value=([], MagicMock()))
            if not hasattr(mock, 'decision_engine'):
                mock.decision_engine = MagicMock()
            if not hasattr(mock.decision_engine, 'ai_engine'):
                mock.decision_engine.ai_engine = MagicMock()
            if not hasattr(mock, 'hr'):
                mock.hr = MagicMock()
            mock.hr.employees = []

            # Helper to return financial snapshot matching the data
            mock.get_financial_snapshot = MagicMock(return_value={
                "total_assets": f_data.get("assets", 0),
                "working_capital": f_data.get("assets", 0),
                "retained_earnings": f_data.get("retained_earnings", 0),
                "average_profit": f_data.get("current_profit", 0),
                "total_debt": f_data.get("total_debt", 0)
            })
            mocks.append(mock)
        return mocks

    def create_firm_dto_list(self) -> List[FirmStateDTO]:
        """Creates actual FirmStateDTO objects from golden data."""
        dtos = []
        for f_data in self.firms_data:
            dto = FirmStateDTO(
                id=f_data.get("id", 0),
                assets=f_data.get("assets", 0.0),
                is_active=f_data.get("is_active", True),
                inventory=f_data.get("inventory", {}),
                inventory_quality={},
                input_inventory={},
                current_production=0.0,
                productivity_factor=f_data.get("productivity_factor", 1.0),
                production_target=100.0,
                capital_stock=100.0,
                base_quality=1.0,
                automation_level=0.0,
                specialization=f_data.get("specialization", "food"),
                total_shares=100.0,
                treasury_shares=0.0,
                dividend_rate=0.1,
                is_publicly_traded=True,
                valuation=1000.0,
                revenue_this_turn=0.0,
                expenses_this_tick=0.0,
                consecutive_loss_turns=f_data.get("consecutive_loss_turns", 0),
                altman_z_score=3.0,
                price_history={},
                profit_history=[f_data.get("current_profit", 0.0)],
                brand_awareness=0.0,
                perceived_quality=1.0,
                marketing_budget=0.0,
                employees=[],
                employees_data={},
                agent_data=f_data,
                system2_guidance={}
            )
            dtos.append(dto)
        return dtos

    def create_config_mock(self):
        """Create a mock config module from golden data."""
        return self.dict_to_mock(self.config_snapshot)
