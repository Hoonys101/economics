import unittest
from unittest.mock import MagicMock, Mock, PropertyMock
import pytest

from modules.finance.call_market.service import CallMarketService
from modules.finance.call_market.api import CallLoanRequestDTO, CallLoanOfferDTO, InsufficientReservesError
from simulation.finance.api import ISettlementSystem
from modules.system.api import IAgentRegistry, DEFAULT_CURRENCY

class TestCallMarketService(unittest.TestCase):
    def setUp(self):
        self.mock_settlement = MagicMock(spec=ISettlementSystem)
        self.mock_registry = MagicMock(spec=IAgentRegistry)
        self.mock_config = MagicMock()
        self.mock_config.TICKS_PER_YEAR = 100.0
        self.mock_config.CALL_MARKET_LOAN_DURATION = 1

        self.service = CallMarketService(
            settlement_system=self.mock_settlement,
            agent_registry=self.mock_registry,
            config_module=self.mock_config
        )

    def test_submit_loan_request(self):
        request = CallLoanRequestDTO(borrower_id=1, amount=100.0, max_interest_rate=0.05)
        self.service.submit_loan_request(request)
        self.assertEqual(len(self.service.pending_requests), 1)
        self.assertEqual(self.service.pending_requests[0], request)

    def test_submit_loan_offer_insufficient_reserves(self):
        offer = CallLoanOfferDTO(lender_id=2, amount=100.0, min_interest_rate=0.04)

        # Mock lender with low balance
        mock_lender = MagicMock()
        mock_lender.wallet.get_balance.return_value = 50.0
        self.mock_registry.get_agent.return_value = mock_lender

        with self.assertRaises(InsufficientReservesError):
            self.service.submit_loan_offer(offer)

    def test_submit_loan_offer_success(self):
        offer = CallLoanOfferDTO(lender_id=2, amount=100.0, min_interest_rate=0.04)

        # Mock lender with sufficient balance
        mock_lender = MagicMock()
        mock_lender.wallet.get_balance.return_value = 150.0
        self.mock_registry.get_agent.return_value = mock_lender

        self.service.submit_loan_offer(offer)
        self.assertEqual(len(self.service.pending_offers), 1)

    def test_clear_market_matching(self):
        # Setup Requests: Borrower A wants 100 @ max 5%, Borrower B wants 50 @ max 4%
        req1 = CallLoanRequestDTO(borrower_id=1, amount=100.0, max_interest_rate=0.05)
        req2 = CallLoanRequestDTO(borrower_id=3, amount=50.0, max_interest_rate=0.04)
        self.service.submit_loan_request(req1)
        self.service.submit_loan_request(req2)

        # Setup Offers: Lender X offers 80 @ min 3%, Lender Y offers 100 @ min 4.5%
        # Mock Lenders
        lender_x = MagicMock()
        lender_x.wallet.get_balance.return_value = 1000.0
        lender_y = MagicMock()
        lender_y.wallet.get_balance.return_value = 1000.0

        # Mock Borrowers
        borrower_a = MagicMock()
        borrower_b = MagicMock()

        def get_agent_side_effect(agent_id):
            if agent_id == 2: return lender_x
            if agent_id == 4: return lender_y
            if agent_id == 1: return borrower_a
            if agent_id == 3: return borrower_b
            return None
        self.mock_registry.get_agent.side_effect = get_agent_side_effect

        off1 = CallLoanOfferDTO(lender_id=2, amount=80.0, min_interest_rate=0.03)
        off2 = CallLoanOfferDTO(lender_id=4, amount=100.0, min_interest_rate=0.045)

        self.service.submit_loan_offer(off1)
        self.service.submit_loan_offer(off2)

        # Mock Settlement Success
        self.mock_settlement.transfer.return_value = {"status": "COMPLETED"}

        # Run Clearing
        result = self.service.clear_market(tick=10)

        # EXPECTATIONS:
        # 1. Sort Requests: Req1 (5%), Req2 (4%)
        # 2. Sort Offers: Off1 (3%), Off2 (4.5%)

        # Match 1: Req1 (5%) vs Off1 (3%)
        #   - Rate: (5+3)/2 = 4%
        #   - Vol: min(100, 80) = 80
        #   - Remaining: Req1=20, Off1=0

        # Match 2: Req1 (rem 20, 5%) vs Off2 (4.5%)
        #   - Rate: (5+4.5)/2 = 4.75%
        #   - Vol: min(20, 100) = 20
        #   - Remaining: Req1=0, Off2=80

        # Match 3: Req2 (50, 4%) vs Off2 (rem 80, 4.5%)
        #   - Condition: 4% >= 4.5% -> FALSE. No match.

        # Total Volume: 80 + 20 = 100
        # Weighted Rate: (80*0.04 + 20*0.0475) / 100 = (3.2 + 0.95) / 100 = 4.15 / 100 = 0.0415

        self.assertAlmostEqual(result['cleared_volume'], 100.0)
        self.assertAlmostEqual(result['weighted_average_rate'], 0.0415)
        self.assertEqual(len(result['matched_loans']), 2)

        # Verify Settlements called
        # Call 1: 80 from 2 to 1
        # Call 2: 20 from 4 to 1
        self.assertEqual(self.mock_settlement.transfer.call_count, 2)
        # Verify tick was passed
        args, kwargs = self.mock_settlement.transfer.call_args_list[0]
        self.assertEqual(kwargs['tick'], 10)

    def test_settle_matured_loans(self):
        # Setup Active Loan
        # 100 loan, 5% rate, 1 year duration (100 ticks), originated at tick 0.
        # Interest = 100 * 0.05 * 1 = 5.0
        # Repayment = 105.0

        loan_id = "test-loan"
        loan = {
            "loan_id": loan_id,
            "lender_id": 2,
            "borrower_id": 1,
            "amount": 100.0,
            "interest_rate": 0.05,
            "origination_tick": 0,
            "maturity_tick": 100
        }
        self.service.active_loans[loan_id] = loan

        # Tick 99: Not matured
        self.service.settle_matured_loans(tick=99)
        self.assertEqual(len(self.service.active_loans), 1)
        self.mock_settlement.transfer.assert_not_called()

        # Tick 100: Matured
        self.mock_registry.get_agent.return_value = MagicMock() # Return mocks for agents
        self.mock_settlement.transfer.return_value = {"status": "COMPLETED"}

        self.service.settle_matured_loans(tick=100)

        self.assertEqual(len(self.service.active_loans), 0)

        # Verify Repayment Transfer
        # Amount = 105.0
        self.mock_settlement.transfer.assert_called_once()
        args, kwargs = self.mock_settlement.transfer.call_args
        self.assertAlmostEqual(kwargs['amount'], 105.0)
        self.assertEqual(kwargs['tick'], 100)
        self.assertEqual(kwargs['credit_agent'], self.mock_registry.get_agent(2)) # Lender gets credit
        self.assertEqual(kwargs['debit_agent'], self.mock_registry.get_agent(1))  # Borrower gets debit

if __name__ == '__main__':
    unittest.main()
