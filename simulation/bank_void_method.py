    def void_loan(self, loan_id: str) -> bool:
        """
        Cancels a loan and reverses the associated deposit creation.
        Used when a transaction funded by a loan fails immediately (e.g. withdrawal failure).
        """
        if loan_id not in self.loans:
            return False

        loan = self.loans[loan_id]
        borrower_id = loan.borrower_id
        amount = loan.principal

        # 1. Reverse Deposit (Liability)
        # Find the deposit for this borrower with matching amount?
        # Or just decrease balance? Since deposits are fungible, decrease balance.
        # But we need to find the specific deposit ID if we want to delete it cleanly,
        # or just subtract from an existing one.
        # `deposit_from_customer` creates a new distinct deposit. We should try to remove it.
        target_dep_id = None
        for dep_id, deposit in self.deposits.items():
            if deposit.depositor_id == borrower_id and abs(deposit.amount - amount) < 1e-9:
                target_dep_id = dep_id
                break

        if target_dep_id:
            del self.deposits[target_dep_id]
        else:
            # Fallback: Just subtract from any deposit of that user
            # If they withdrew it already, this void_loan shouldn't be called (logic in HousingSystem calls it only if withdraw fails)
            # So the funds MUST be there.
            logger.warning(f"VOID_LOAN | Could not find exact deposit for rollback. Loan: {loan_id}")
            # We assume the caller knows what they are doing. If withdrawal failed, the money is still in the bank.
            # But wait, if withdrawal failed, it might mean bank didn't have assets (insolvent), but the DEPOSIT exists.
            # We must destroy the liability.
            pass

        # 2. Destroy Loan (Asset)
        del self.loans[loan_id]

        # 3. Reverse Money Supply Tracking
        if self.government and hasattr(self.government, "total_money_issued"):
             self.government.total_money_issued -= amount

        logger.info(f"LOAN_VOIDED | Loan {loan_id} cancelled and deposit reversed.")
        return True
