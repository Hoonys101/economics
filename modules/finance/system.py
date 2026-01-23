from typing import List, Dict, Optional, Any
import logging
from modules.finance.api import IFinanceSystem, BondDTO, BailoutLoanDTO, BailoutCovenant, IFinancialEntity, InsufficientFundsError
from modules.finance.domain import AltmanZScoreCalculator
from modules.analysis.fiscal_monitor import FiscalMonitor
# Forward reference for type hinting
from simulation.firms import Firm

logger = logging.getLogger(__name__)

class FinanceSystem(IFinanceSystem):
    """Manages sovereign debt, corporate bailouts, and solvency checks."""

    def __init__(self, government: 'Government', central_bank: 'CentralBank', bank: 'Bank', config_module: Any, settlement_system: Any = None):
        self.government = government
        self.central_bank = central_bank
        self.bank = bank
        self.config_module = config_module
        self.settlement_system = settlement_system
        self.outstanding_bonds: List[BondDTO] = []
        self.fiscal_monitor = FiscalMonitor()

        if not self.settlement_system:
            logger.warning("FinanceSystem initialized without SettlementSystem. Strict mode transfers will fail.")

    def evaluate_solvency(self, firm: 'Firm', current_tick: int) -> bool:
        """Evaluates a firm's solvency to determine bailout eligibility."""
        startup_grace_period = self.config_module.get("economy_params.STARTUP_GRACE_PERIOD_TICKS", 24)
        z_score_threshold = self.config_module.get("economy_params.ALTMAN_Z_SCORE_THRESHOLD", 1.81)

        if firm.age < startup_grace_period:
            # Runway Check for startups
            monthly_wage_bill = firm.hr.get_total_wage_bill() * 4  # Approximate monthly
            required_runway = monthly_wage_bill * 3
            return firm.cash_reserve >= required_runway
        else:
            # Altman Z-Score for established firms
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

        # Use FiscalMonitor for risk assessment
        world_dto = getattr(self.government, 'sensory_data', None)
        debt_to_gdp = self.fiscal_monitor.get_debt_to_gdp_ratio(self.government, world_dto)

        # Config-driven risk premium tiers
        risk_premium_tiers = self.config_module.get("economy_params.DEBT_RISK_PREMIUM_TIERS", {
            1.2: 0.05,
            0.9: 0.02,
            0.6: 0.005,
        })

        risk_premium = 0.0
        # Convert keys to floats just in case they are strings in the dictionary
        sorted_tiers = sorted(
            [(float(k), v) for k, v in risk_premium_tiers.items()],
            key=lambda x: x[0],
            reverse=True
        )

        for threshold, premium in sorted_tiers:
            if debt_to_gdp > threshold:
                risk_premium = premium
                break

        yield_rate = base_rate + risk_premium

        bond_maturity = self.config_module.get("economy_params.BOND_MATURITY_TICKS", 400)
        new_bond = BondDTO(
            id=f"BOND_{current_tick}_{len(self.outstanding_bonds)}",
            issuer="GOVERNMENT",
            face_value=amount,
            yield_rate=yield_rate,
            maturity_date=current_tick + bond_maturity
        )

        qe_threshold = self.config_module.get("economy_params.QE_INTERVENTION_YIELD_THRESHOLD", 0.10)
        buyer = None

        if yield_rate > qe_threshold:
            # Central Bank intervenes as buyer of last resort (QE)
            buyer = self.central_bank
            # Note: Central Bank purchasing logic (add to portfolio) should be handled
        else:
            # Commercial bank buys it
            if self.bank.assets >= amount:
                buyer = self.bank
            else:
                # Bond issuance fails if no one can buy it
                logger.warning("BOND_ISSUANCE_FAILED | No buyer found (Bank insufficient funds).")
                return []

        # Execute Transfer via SettlementSystem
        memo = f"Govt Bond Sale {new_bond.id}, Yield: {yield_rate:.2%}"
        if self._transfer(debtor=buyer, creditor=self.government, amount=amount, memo=memo):
            self.outstanding_bonds.append(new_bond)

            # Update Buyer Portfolio
            if hasattr(buyer, 'add_bond_to_portfolio'):
                buyer.add_bond_to_portfolio(new_bond)
            elif buyer == self.central_bank:
                # Central Bank logic (if add_bond_to_portfolio missing)
                if not hasattr(buyer.assets, 'get'): # If assets is not dict
                     # Assuming CentralBank implementation, but for now specific hack
                     pass
                if isinstance(buyer.assets, dict):
                     if "bonds" not in buyer.assets:
                         buyer.assets["bonds"] = []
                     buyer.assets["bonds"].append(new_bond)

            return [new_bond]
        else:
             logger.error("BOND_ISSUANCE_FAILED | Settlement failed.")
             return []

    def collect_corporate_tax(self, firm: IFinancialEntity, tax_amount: float) -> bool:
        """Collects corporate tax using atomic settlement."""
        memo = f"Corporate Tax, Firm ID: {firm.id}"
        return self._transfer(
            debtor=firm,
            creditor=self.government,
            amount=tax_amount,
            memo=memo
        )

    def grant_bailout_loan(self, firm: 'Firm', amount: float) -> Optional[BailoutLoanDTO]:
        """
        Converts a bailout from a grant to an interest-bearing senior loan.
        Returns the loan DTO on success, or None if the transfer fails.
        """
        base_rate = self.central_bank.get_base_rate()
        penalty_premium = self.config_module.get("economy_params.BAILOUT_PENALTY_PREMIUM", 0.05)

        covenants = BailoutCovenant(
            dividends_allowed=False,
            executive_salary_freeze=True,
            mandatory_repayment=self.config_module.get("economy_params.BAILOUT_COVENANT_RATIO", 0.5)
        )
        loan = BailoutLoanDTO(
            firm_id=firm.id,
            amount=amount,
            interest_rate=base_rate + penalty_premium,
            covenants=covenants
        )

        # Transfer funds from Government to the firm
        if self._transfer(debtor=self.government, creditor=firm, amount=amount, memo=f"Bailout Loan {firm.id}"):
            # The government provides the funds, which become a liability for the firm
            firm.finance.add_liability(amount, loan.interest_rate)
            firm.has_bailout_loan = True
            return loan
        else:
            logger.error(f"BAILOUT_FAILED | Could not transfer {amount:.2f} to Firm {firm.id} for bailout.")
            return None


    def _transfer(self, debtor: IFinancialEntity, creditor: IFinancialEntity, amount: float, memo: str = "FinanceSystem Transfer") -> bool:
        """
        Atomically handles the movement of funds using SettlementSystem.
        Strict Mode: Fails if SettlementSystem is missing.
        """
        if amount <= 0:
            return True

        if self.settlement_system:
            return self.settlement_system.transfer(debtor, creditor, amount, memo)

        logger.critical(
            f"TRANSFER_FAILED | SettlementSystem not available for transfer of {amount:.2f} from {debtor.id} to {creditor.id}. Strict Mode enforced.",
            extra={"tags": ["finance_system", "strict_mode_error"]}
        )
        return False

    def service_debt(self, current_tick: int) -> None:
        """
        Manages the servicing of outstanding government debt.
        When bonds mature, both principal and accrued simple interest are paid.
        """
        matured_bonds = [b for b in self.outstanding_bonds if b.maturity_date <= current_tick]

        bond_maturity_ticks = self.config_module.get("economy_params.BOND_MATURITY_TICKS", 400)
        ticks_per_year = getattr(self.config_module, "TICKS_PER_YEAR", 48)

        for bond in matured_bonds:
            # Calculate simple interest accrued over the bond's lifetime
            interest_amount = bond.face_value * bond.yield_rate * (bond_maturity_ticks / ticks_per_year)
            total_repayment = bond.face_value + interest_amount

            # Identify bond holder
            bond_holder = self.bank # Default

            # Check Central Bank
            if hasattr(self.central_bank, 'assets') and isinstance(self.central_bank.assets, dict):
                 if bond in self.central_bank.assets.get("bonds", []):
                      bond_holder = self.central_bank

            # Execute Repayment via SettlementSystem
            memo = f"Bond Repayment {bond.id}"
            if self._transfer(debtor=self.government, creditor=bond_holder, amount=total_repayment, memo=memo):
                 # Post-settlement cleanup
                 if bond_holder == self.central_bank:
                      self.central_bank.assets["bonds"].remove(bond)
                 # Note: If Commercial Bank, we assume it just takes cash.
                 # If it had a specific list of bonds, we should remove it there too.

                 self.outstanding_bonds.remove(bond)
            else:
                 logger.critical(f"SOVEREIGN_DEFAULT | Government failed to repay bond {bond.id} (Amt: {total_repayment:.2f})")
                 # Future: Trigger Default Protocol
