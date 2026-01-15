from typing import List, Dict
from modules.finance.api import IFinanceSystem, BondDTO, BailoutLoanDTO
# Forward reference for type hinting
from simulation.firms import Firm

class FinanceSystem(IFinanceSystem):
    """Manages sovereign debt, corporate bailouts, and solvency checks."""

    def __init__(self, government: 'Government', central_bank: 'CentralBank', config_module: any):
        self.government = government
        self.central_bank = central_bank
        self.config_module = config_module
        self.outstanding_bonds: List[BondDTO] = []

    def evaluate_solvency(self, firm: 'Firm', current_tick: int) -> bool:
        """
        Evaluates a firm's solvency to determine bailout eligibility.
        - Startups (< 24 ticks old) are checked for a 3-month wage runway.
        - Established firms are evaluated using the Altman Z-Score.
        """
        startup_grace_period = getattr(self.config_module, "STARTUP_GRACE_PERIOD_TICKS", 24)
        z_score_threshold = getattr(self.config_module, "ALTMAN_Z_SCORE_THRESHOLD", 1.81)

        if firm.age < startup_grace_period:
            # Runway Check for startups
            monthly_wage_bill = firm.hr.get_total_wage_bill() * 4  # Approximate monthly
            required_runway = monthly_wage_bill * 3
            return firm.assets >= required_runway
        else:
            # Altman Z-Score for established firms
            z_score = firm.finance.calculate_altman_z_score()
            return z_score > z_score_threshold

    def issue_treasury_bonds(self, amount: float, current_tick: int) -> List[BondDTO]:
        """
        Issues new treasury bonds to the market.
        Yield is determined by the base rate plus a risk premium based on Debt-to-GDP ratio.
        """
        # This is a simplified auction. A real implementation would involve market participants.
        base_rate = self.central_bank.get_interest_rate()
        debt_to_gdp = self.government.get_debt_to_gdp_ratio()

        # Exponential risk premium
        risk_premium = 0.0
        if debt_to_gdp > 1.2:
            risk_premium = 0.05
        elif debt_to_gdp > 0.9:
            risk_premium = 0.02
        elif debt_to_gdp > 0.6:
            risk_premium = 0.005

        yield_rate = base_rate + risk_premium

        # For now, assume the central bank buys all bonds as the buyer of last resort
        new_bond = BondDTO(
            id=f"BOND_{current_tick}",
            issuer="GOVERNMENT",
            face_value=amount,
            yield_rate=yield_rate,
            maturity_date=current_tick + getattr(self.config_module, "BOND_MATURITY_TICKS", 400) # 4 years
        )
        self.outstanding_bonds.append(new_bond)
        self.central_bank.purchase_bonds(new_bond)
        self.government.assets += amount

        return [new_bond]

    def grant_bailout_loan(self, firm: 'Firm', amount: float) -> BailoutLoanDTO:
        """Converts a bailout from a grant to an interest-bearing senior loan."""
        base_rate = self.central_bank.get_interest_rate()
        penalty_premium = getattr(self.config_module, "BAILOUT_PENALTY_PREMIUM", 0.05)

        loan = BailoutLoanDTO(
            firm_id=firm.id,
            amount=amount,
            interest_rate=base_rate + penalty_premium,
            covenants={
                "dividends_allowed": False,
                "executive_salary_freeze": True
            }
        )

        # The government provides the funds, which become a liability for the firm
        self.government.assets -= amount
        firm.finance.add_liability(amount, loan.interest_rate)

        return loan


    def service_debt(self, current_tick: int) -> None:
        """Manages the servicing of outstanding government debt."""
        # This is a simplified version. A real implementation would handle interest payments
        # and bond maturation.
        matured_bonds = [b for b in self.outstanding_bonds if b.maturity_date <= current_tick]
        for bond in matured_bonds:
            self.government.assets -= bond.face_value
            self.outstanding_bonds.remove(bond)
