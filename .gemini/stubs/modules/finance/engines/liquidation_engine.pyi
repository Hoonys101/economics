from modules.finance.engine_api import EngineOutputDTO as EngineOutputDTO, FinancialLedgerDTO as FinancialLedgerDTO, ILiquidationEngine as ILiquidationEngine, LiquidationRequestDTO as LiquidationRequestDTO

class LiquidationEngine(ILiquidationEngine):
    """
    Stateless engine to liquidate a firm.
    MIGRATION: Uses integer pennies.
    """
    def liquidate(self, request: LiquidationRequestDTO, ledger: FinancialLedgerDTO) -> EngineOutputDTO: ...
