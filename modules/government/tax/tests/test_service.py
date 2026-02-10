import unittest
from unittest.mock import MagicMock, patch
from modules.government.tax.service import TaxService
from modules.finance.api import TaxCollectionResult
from modules.government.dtos import FiscalPolicyDTO
from modules.system.api import DEFAULT_CURRENCY

class TestTaxService(unittest.TestCase):
    def setUp(self):
        self.config_mock = MagicMock()

    @patch('modules.government.tax.service.TaxationSystem')
    @patch('modules.government.tax.service.FiscalPolicyManager')
    def test_initialization(self, MockFiscalPolicyManager, MockTaxationSystem):
        service = TaxService(self.config_mock)

        MockTaxationSystem.assert_called_with(self.config_mock)
        MockFiscalPolicyManager.assert_called_with(self.config_mock)

        self.assertEqual(service.total_collected_tax[DEFAULT_CURRENCY], 0.0)
        self.assertEqual(service.revenue_this_tick[DEFAULT_CURRENCY], 0.0)

    @patch('modules.government.tax.service.TaxationSystem')
    @patch('modules.government.tax.service.FiscalPolicyManager')
    def test_calculate_tax_liability(self, MockFiscalPolicyManager, MockTaxationSystem):
        service = TaxService(self.config_mock)
        mock_fpm = MockFiscalPolicyManager.return_value
        mock_fpm.calculate_tax_liability.return_value = 100.0

        policy = MagicMock(spec=FiscalPolicyDTO)
        result = service.calculate_tax_liability(policy, 1000.0)

        mock_fpm.calculate_tax_liability.assert_called_with(policy, 1000.0)
        self.assertEqual(result, 100.0)

    @patch('modules.government.tax.service.TaxationSystem')
    @patch('modules.government.tax.service.FiscalPolicyManager')
    def test_calculate_corporate_tax(self, MockFiscalPolicyManager, MockTaxationSystem):
        service = TaxService(self.config_mock)
        mock_ts = MockTaxationSystem.return_value
        mock_ts.calculate_corporate_tax.return_value = 50.0

        result = service.calculate_corporate_tax(500.0, 0.1)

        mock_ts.calculate_corporate_tax.assert_called_with(500.0, 0.1)
        self.assertEqual(result, 50.0)

    @patch('modules.government.tax.service.TaxationSystem')
    @patch('modules.government.tax.service.FiscalPolicyManager')
    def test_record_revenue(self, MockFiscalPolicyManager, MockTaxationSystem):
        service = TaxService(self.config_mock)

        result_data: TaxCollectionResult = {
            "success": True,
            "amount_collected": 100.0,
            "tax_type": "income_tax",
            "payer_id": "agent_1",
            "payee_id": "gov_1",
            "error_message": None,
            "currency": DEFAULT_CURRENCY
        }

        service.record_revenue(result_data)

        self.assertEqual(service.revenue_this_tick[DEFAULT_CURRENCY], 100.0)
        self.assertEqual(service.total_collected_tax[DEFAULT_CURRENCY], 100.0)
        self.assertEqual(service.current_tick_stats["tax_revenue"]["income_tax"], 100.0)
        self.assertEqual(service.current_tick_stats["total_collected"], 100.0)

    @patch('modules.government.tax.service.TaxationSystem')
    @patch('modules.government.tax.service.FiscalPolicyManager')
    def test_record_revenue_failure(self, MockFiscalPolicyManager, MockTaxationSystem):
        service = TaxService(self.config_mock)

        result_data: TaxCollectionResult = {
            "success": False,
            "amount_collected": 100.0,
            "tax_type": "income_tax",
            "payer_id": "agent_1",
            "payee_id": "gov_1",
            "error_message": "Failed"
        }

        service.record_revenue(result_data)

        self.assertEqual(service.revenue_this_tick[DEFAULT_CURRENCY], 0.0)

    @patch('modules.government.tax.service.TaxationSystem')
    @patch('modules.government.tax.service.FiscalPolicyManager')
    def test_reset_tick_flow(self, MockFiscalPolicyManager, MockTaxationSystem):
        service = TaxService(self.config_mock)

        # Setup some state
        service.revenue_this_tick["USD"] = 100.0
        service.current_tick_stats["total_collected"] = 100.0

        service.reset_tick_flow()

        self.assertEqual(service.revenue_this_tick, {DEFAULT_CURRENCY: 0.0})
        self.assertEqual(service.current_tick_stats["total_collected"], 0.0)
        self.assertEqual(service.current_tick_stats["tax_revenue"], {})
