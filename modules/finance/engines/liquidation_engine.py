from modules.finance.engine_api import (
    ILiquidationEngine, LiquidationRequestDTO, FinancialLedgerDTO, EngineOutputDTO
)
from simulation.models import Transaction

class LiquidationEngine(ILiquidationEngine):
    """
    Stateless engine to liquidate a firm.
    """

    def liquidate(
        self,
        request: LiquidationRequestDTO,
        ledger: FinancialLedgerDTO
    ) -> EngineOutputDTO:

        txs = []

        # 1. Sell Inventory (Abstracted as instant sale at discount)
        liquidation_value = request.inventory_value * 0.5 # Fire sale discount

        if liquidation_value > 0:
            txs.append(Transaction(
                buyer_id="MARKET_LIQUIDITY", # Placeholder
                seller_id=request.firm_id,
                item_id="liquidation_inventory",
                quantity=1,
                price=liquidation_value,
                market_id="liquidation",
                transaction_type="liquidation_sale",
                time=ledger.current_tick
            ))

        # 2. Settle Debts
        # This engine needs to know WHICH bank holds the debt.
        # Currently LiquidationRequestDTO has `outstanding_debt` float, but not who to pay.
        # We should look up the loans in the ledger for this firm.

        total_proceeds = liquidation_value + request.capital_value
        remaining_proceeds = total_proceeds

        # Find loans for this firm
        firm_loans = []
        for bank_id, bank in ledger.banks.items():
            for loan_id, loan in bank.loans.items():
                if loan.borrower_id == request.firm_id and not loan.is_defaulted:
                    firm_loans.append((bank_id, loan))

        # Pay off loans
        for bank_id, loan in firm_loans:
            repayment = min(remaining_proceeds, loan.remaining_principal)
            if repayment > 0:
                loan.remaining_principal -= repayment
                # [Double-Entry] Credit Bank Reserves (Cash Receipt)
                # Asset (Loan) Down, Asset (Reserves) Up.
                if bank_id in ledger.banks:
                    # Assuming default currency for now
                    from modules.system.api import DEFAULT_CURRENCY
                    reserves = ledger.banks[bank_id].reserves
                    if DEFAULT_CURRENCY not in reserves: reserves[DEFAULT_CURRENCY] = 0.0
                    reserves[DEFAULT_CURRENCY] += repayment

                remaining_proceeds -= repayment

                txs.append(Transaction(
                    buyer_id=request.firm_id,
                    seller_id=bank_id,
                    item_id=loan.loan_id,
                    quantity=1,
                    price=repayment,
                    market_id="financial",
                    transaction_type="loan_repayment_liquidation",
                    time=ledger.current_tick
                ))

            if loan.remaining_principal > 0:
                # Default the rest
                loan.is_defaulted = True
                default_amount = loan.remaining_principal

                # [Double-Entry] Write-off: Asset (Loan) Down, Equity (Retained Earnings) Down
                if bank_id in ledger.banks:
                     ledger.banks[bank_id].retained_earnings -= default_amount

                loan.remaining_principal = 0 # Write off from active balance

                txs.append(Transaction(
                    buyer_id=request.firm_id, # Or Bank?
                    seller_id=bank_id,
                    item_id=loan.loan_id,
                    quantity=1,
                    price=default_amount,
                    market_id="financial",
                    transaction_type="loan_default",
                    time=ledger.current_tick
                ))

        # 3. Distribute remaining equity (if any)
        if remaining_proceeds > 0:
             txs.append(Transaction(
                buyer_id="SHAREHOLDERS", # Placeholder
                seller_id=request.firm_id,
                item_id="liquidation_residue",
                quantity=1,
                price=remaining_proceeds,
                market_id="financial",
                transaction_type="equity_distribution",
                time=ledger.current_tick
             ))

        return EngineOutputDTO(
            updated_ledger=ledger,
            generated_transactions=txs
        )
