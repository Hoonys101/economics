from typing import List, Dict, Optional
import logging
from modules.finance.api import IFinanceSystem, BondDTO, BailoutLoanDTO, BailoutCovenant, IFinancialEntity, InsufficientFundsError
from modules.finance.domain import AltmanZScoreCalculator
# Forward reference for type hinting
from simulation.firms import Firm

logger = logging.getLogger(__name__)

class FinanceSystem(IFinanceSystem):
    """Manages sovereign debt, corporate bailouts, and solvency checks."""

    def __init__(self, government: 'Government', central_bank: 'CentralBank', bank: 'Bank', config_module: any):
        self.government = government
        self.central_bank = central_bank
        self.bank = bank
        self.config_module = config_module
        self.outstanding_bonds: List[BondDTO] = []

    def evaluate_solvency(self, firm: 'Firm', current_tick: int) -> bool:
        """Evaluates a firm's solvency to determine bailout eligibility.

        This method uses two distinct evaluation paths based on the firm's age:
        1.  **Startup Runway Check**: For new firms still within their grace period
            (defined by `STARTUP_GRACE_PERIOD_TICKS` from the config), solvency
            is determined by their cash runway. The check ensures they have enough
            cash reserves to cover their wage bill for a defined period (e.g., 3 months).
        2.  **Altman Z-Score**: For established firms beyond the grace period,
            solvency is assessed using the Altman Z-Score, a more comprehensive
            financial health metric. A score above the `ALTMAN_Z_SCORE_THRESHOLD`
            (from the config) is considered solvent.

        Args:
            firm: The firm entity to be evaluated.
            current_tick: The current simulation tick, used for age calculation.

        Returns:
            True if the firm is deemed solvent and thus ineligible for a bailout,
            False otherwise.
        """
        startup_grace_period = getattr(self.config_module, "STARTUP_GRACE_PERIOD_TICKS", 24)
        z_score_threshold = getattr(self.config_module, "ALTMAN_Z_SCORE_THRESHOLD", 1.81)

        if firm.age < startup_grace_period:
            # Runway Check for startups
            monthly_wage_bill = firm.hr.get_total_wage_bill() * 4  # Approximate monthly
            required_runway = monthly_wage_bill * 3
            return firm.cash_reserve >= required_runway
        else:
            # Altman Z-Score for established firms
            # Extracted data gathering to decouple from FinanceDepartment logic
            total_assets = firm.assets + firm.capital_stock + firm.get_inventory_value()
            working_capital = firm.assets - getattr(firm, 'total_debt', 0.0)
            retained_earnings = firm.finance.retained_earnings

            # Safe calculation of average profit
            profit_history = firm.finance.profit_history
            average_profit = sum(profit_history) / len(profit_history) if profit_history else 0.0

            z_score = AltmanZScoreCalculator.calculate(
                total_assets=total_assets,
                working_capital=working_capital,
                retained_earnings=retained_earnings,
                average_profit=average_profit
            )
            return z_score > z_score_threshold

    def issue_treasury_bonds(self, amount: float, current_tick: int) -> List[BondDTO]:
        """
        Issues new treasury bonds to the market, allowing for crowding out.
        The Central Bank only intervenes if yields exceed a critical threshold.
        """
        base_rate = self.central_bank.get_base_rate()
        debt_to_gdp = self.government.get_debt_to_gdp_ratio()

        # Config-driven risk premium tiers
        risk_premium_tiers = self.config_module.get("economy_params.debt_risk_premium_tiers", {
            1.2: 0.05,
            0.9: 0.02,
            0.6: 0.005,
        })

        risk_premium = 0.0
        for threshold, premium in sorted(risk_premium_tiers.items(), reverse=True):
            if debt_to_gdp > threshold:
                risk_premium = premium
                break

        yield_rate = base_rate + risk_premium

        bond_maturity = self.config_module.get("economy_params.bond_maturity_ticks", 400)
        new_bond = BondDTO(
            id=f"BOND_{current_tick}",
            issuer="GOVERNMENT",
            face_value=amount,
            yield_rate=yield_rate,
            maturity_date=current_tick + bond_maturity
        )

        qe_threshold = self.config_module.get("economy_params.qe_intervention_yield_threshold", 0.10)
        if yield_rate > qe_threshold:
            # Central Bank intervenes as buyer of last resort (QE)
            self.central_bank.purchase_bonds(new_bond)
            # Transfer funds from Central Bank to Government
            self._transfer(debtor=self.central_bank, creditor=self.government, amount=amount)
        else:
            # Sell to the market (commercial bank buys it)
            if self.bank.assets >= amount:
                # Transfer funds from commercial bank to Government
                self._transfer(debtor=self.bank, creditor=self.government, amount=amount)
            else:
                # Bond issuance fails if no one can buy it
                return []

        self.outstanding_bonds.append(new_bond)
        return [new_bond]

    def grant_bailout_loan(self, firm: 'Firm', amount: float) -> Optional[BailoutLoanDTO]:
        """
        Converts a bailout from a grant to an interest-bearing senior loan.
        Returns the loan DTO on success, or None if the transfer fails.
        """
        base_rate = self.central_bank.get_base_rate()
        penalty_premium = self.config_module.get("economy_params.bailout_penalty_premium", 0.05)

        covenants = BailoutCovenant(
            dividends_allowed=False,
            executive_salary_freeze=True,
            mandatory_repayment=self.config_module.get("economy_params.bailout_repayment_ratio", 0.5)
        )
        loan = BailoutLoanDTO(
            firm_id=firm.id,
            amount=amount,
            interest_rate=base_rate + penalty_premium,
            covenants=covenants
        )

        # Transfer funds from Government to the firm
        if self._transfer(debtor=self.government, creditor=firm, amount=amount):
            # The government provides the funds, which become a liability for the firm
            firm.finance.add_liability(amount, loan.interest_rate)
            firm.has_bailout_loan = True
            return loan
        else:
            logger.error(f"BAILOUT_FAILED | Could not transfer {amount:.2f} to Firm {firm.id} for bailout.")
            return None


    def _transfer(self, debtor: IFinancialEntity, creditor: IFinancialEntity, amount: float) -> bool:
        """
        Atomically handles the movement of funds between two entities using the IFinancialEntity protocol.

        Args:
            debtor: The entity from which money is withdrawn.
            creditor: The entity to which money is deposited.
            amount: The amount of money to transfer.

        Returns:
            True if the transfer was successful, False otherwise.
        """
        if amount <= 0:
            return True # A zero-amount transfer is trivially successful.

        try:
            debtor.withdraw(amount)
            creditor.deposit(amount)
            return True
        except InsufficientFundsError as e:
            logger.warning(f"TRANSFER_FAILED | Atomic transfer of {amount:.2f} failed: {e}")
            return False

    def service_debt(self, current_tick: int) -> None:
        """
        Manages the servicing of outstanding government debt.
        When bonds mature, both principal and accrued simple interest are paid.
        """
        matured_bonds = [b for b in self.outstanding_bonds if b.maturity_date <= current_tick]

        bond_maturity_ticks = self.config_module.get("economy_params.bond_maturity_ticks", 400)
        ticks_per_year = self.config_module.get("TICKS_PER_YEAR", 48)

        for bond in matured_bonds:
            # Calculate simple interest accrued over the bond's lifetime
            interest_amount = bond.face_value * bond.yield_rate * (bond_maturity_ticks / ticks_per_year)
            total_repayment = bond.face_value + interest_amount

            # This is a critical monetary operation. Failure to pay destroys sovereign credit.
            # For now, we assume the government can always pay. A future feature could model default.
            self.government.assets -= total_repayment

            # Money Leak Fix: Transfer the repayment to the bondholder.
            # We need to determine who holds the bond.
            # Simplified: Check if it's on the Central Bank's balance sheet.
            if bond in self.central_bank.assets.get("bonds", []):
                # Central Bank gets the money back (e.g., QE unwind)
                self.central_bank.assets["bonds"].remove(bond)
                # BUG FIX: Transfer the repayment to the Central Bank's assets
                # This prevents the "money destruction" bug.
                self.central_bank.assets["cash"] = self.central_bank.assets.get("cash", 0) + total_repayment
            else:
                # Assume the commercial bank holds it
                self.bank.assets += total_repayment

            # The bond is removed from the outstanding list
            self.outstanding_bonds.remove(bond)
