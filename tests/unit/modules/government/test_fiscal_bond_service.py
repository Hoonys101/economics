import pytest
from unittest.mock import MagicMock
from modules.government.services.fiscal_bond_service import FiscalBondService
from modules.government.dtos import FiscalContextDTO, BondIssueRequestDTO, BondIssuanceResultDTO
from modules.finance.api import BondDTO

class TestFiscalBondService:
    def test_calculate_yield_low_debt(self):
        service = FiscalBondService()
        context = FiscalContextDTO(
            tick=100,
            current_gdp=100000,
            debt_to_gdp_ratio=0.5,
            population_count=100,
            treasury_balance=50000
        )
        # Base (0.03) + Risk(0) + Spread(0.01) = 0.04
        assert service.calculate_yield(context) == pytest.approx(0.04)

    def test_calculate_yield_high_debt(self):
        service = FiscalBondService()
        context = FiscalContextDTO(
            tick=100,
            current_gdp=100000,
            debt_to_gdp_ratio=2.0,
            population_count=100,
            treasury_balance=50000
        )
        # Base (0.03) + Risk((2.0-1.0)*0.02 = 0.02) + Spread(0.01) = 0.06
        assert service.calculate_yield(context) == pytest.approx(0.06)

    def test_issue_bonds_normal_buyer(self):
        service = FiscalBondService()
        request = BondIssueRequestDTO(
            amount_pennies=10000,
            maturity_ticks=400,
            target_yield=0.0
        )
        # Debt/GDP 0.5 < 1.5 QE threshold
        context = FiscalContextDTO(
            tick=100,
            current_gdp=100000,
            debt_to_gdp_ratio=0.5,
            population_count=100,
            treasury_balance=50000
        )

        mock_bank = MagicMock()
        mock_bank.id = 101
        buyer_pool = {"bank": mock_bank}

        result = service.issue_bonds(request, context, buyer_pool)

        assert result.payment_request.payer == mock_bank
        assert result.payment_request.payee == "GOVERNMENT"
        assert result.payment_request.amount == 10000
        assert result.bond_dto.face_value == 10000
        assert result.bond_dto.maturity_date == 500
        assert "BOND_" in result.bond_dto.id

    def test_issue_bonds_qe_buyer(self):
        service = FiscalBondService()
        request = BondIssueRequestDTO(
            amount_pennies=10000,
            maturity_ticks=400,
            target_yield=0.0
        )
        # Debt/GDP 2.0 > 1.5 QE threshold
        context = FiscalContextDTO(
            tick=100,
            current_gdp=100000,
            debt_to_gdp_ratio=2.0,
            population_count=100,
            treasury_balance=50000
        )

        mock_cb = MagicMock()
        mock_cb.id = 999
        mock_bank = MagicMock()
        mock_bank.id = 101
        buyer_pool = {"central_bank": mock_cb, "bank": mock_bank}

        result = service.issue_bonds(request, context, buyer_pool)

        assert result.payment_request.payer == mock_cb
        assert result.bond_dto.yield_rate == pytest.approx(0.06) # Should use calculated yield if target is 0.0

    def test_issue_bonds_no_buyer(self):
        service = FiscalBondService()
        request = BondIssueRequestDTO(
            amount_pennies=10000,
            maturity_ticks=400,
            target_yield=0.0
        )
        context = FiscalContextDTO(
            tick=100,
            current_gdp=100000,
            debt_to_gdp_ratio=0.5,
            population_count=100,
            treasury_balance=50000
        )

        buyer_pool = {} # Empty

        result = service.issue_bonds(request, context, buyer_pool)

        # Should return UNKNOWN_BUYER or similar
        assert result.payment_request.payer == "UNKNOWN_BUYER"
