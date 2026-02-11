from typing import Dict
from modules.finance.engine_api import (
    IInterestRateEngine, FinancialLedgerDTO
)

class InterestRateEngine(IInterestRateEngine):
    """
    Stateless engine to update interest rates.
    """

    def update_rates(
        self,
        economic_indicators: Dict,
        ledger: FinancialLedgerDTO
    ) -> FinancialLedgerDTO:

        # Simple rule: If inflation is high, raise rates.
        inflation = economic_indicators.get("inflation_rate", 0.0)
        target_rate = 0.03 + (inflation * 0.5)

        # Update all banks
        for bank_id, bank in ledger.banks.items():
            bank.base_rate = target_rate

        return ledger
