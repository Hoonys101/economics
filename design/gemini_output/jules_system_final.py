from typing import List, Dict
from modules.finance.api import IFinanceSystem, BondDTO, BailoutLoanDTO

# Forward reference for type hinting
from simulation.firms import Firm


class FinanceSystem(IFinanceSystem):
    """Manages sovereign debt, corporate bailouts, and solvency checks."""

    def __init__(
        self,
        government: "Government",
        central_bank: "CentralBank",
        bank: "Bank",
        config_module: any,
    ):
        self.government = government
        self.central_bank = central_bank
        self.bank = bank
        self.config_module = config_module
        self.outstanding_bonds: List[BondDTO] = []

    def evaluate_solvency(self, firm: "Firm", current_tick: int) -> bool:
        """
        Evaluates a firm's solvency to determine bailout eligibility.
        - Startups (< 24 ticks old) are checked for a 3-month wage runway.
        - Established firms are evaluated using the Altman Z-Score.
        """
        startup_grace_period = getattr(
            self.config_module, "STARTUP_GRACE_PERIOD_TICKS", 24
        )
        z_score_threshold = getattr(
            self.config_module, "ALTMAN_Z_SCORE_THRESHOLD", 1.81
        )

        if firm.age < startup_grace_period:
            # Runway Check for startups
            monthly_wage_bill = firm.hr.get_total_wage_bill() * 4  # Approximate monthly
            required_runway = monthly_wage_bill * 3
            return firm.cash_reserve >= required_runway
        else:
            # Altman Z-Score for established firms
            z_score = firm.finance.calculate_altman_z_score()
            return z_score > z_score_threshold

    def issue_treasury_bonds(self, amount: float, current_tick: int) -> List[BondDTO]:
        """
        Issues new treasury bonds to the market, allowing for crowding out.
        The Central Bank only intervenes if yields exceed a critical threshold.
        """
        base_rate = self.central_bank.get_interest_rate()
        debt_to_gdp = self.government.get_debt_to_gdp_ratio()

        # Config-driven risk premium tiers
        risk_premium_tiers = getattr(
            self.config_module,
            "DEBT_RISK_PREMIUM_TIERS",
            {
                1.2: 0.05,
                0.9: 0.02,
                0.6: 0.005,
            },
        )

        risk_premium = 0.0
        for threshold, premium in sorted(risk_premium_tiers.items(), reverse=True):
            if debt_to_gdp > threshold:
                risk_premium = premium
                break

        yield_rate = base_rate + risk_premium

        bond_maturity = getattr(self.config_module, "BOND_MATURITY_TICKS", 400)
        new_bond = BondDTO(
            id=f"BOND_{current_tick}",
            issuer="GOVERNMENT",
            face_value=amount,
            yield_rate=yield_rate,
            maturity_date=current_tick + bond_maturity,
        )

        qe_threshold = getattr(
            self.config_module, "QE_INTERVENTION_YIELD_THRESHOLD", 0.10
        )
        if yield_rate > qe_threshold:
            # Central Bank intervenes as buyer of last resort
            self.central_bank.purchase_bonds(new_bond)
            # Money is created here, which is the point of QE.
        else:
            # Sell to the market (simplified: the commercial bank buys it)
            if self.bank.assets >= amount:
                self.bank.assets -= amount
            else:
                # Bond issuance fails if no one can buy it
                return []

        self.outstanding_bonds.append(new_bond)
        self.government.assets += amount

        return [new_bond]

    def grant_bailout_loan(self, firm: "Firm", amount: float) -> BailoutLoanDTO:
        """Converts a bailout from a grant to an interest-bearing senior loan."""
        base_rate = self.central_bank.get_interest_rate()
        penalty_premium = getattr(self.config_module, "BAILOUT_PENALTY_PREMIUM", 0.05)

        loan = BailoutLoanDTO(
            firm_id=firm.id,
            amount=amount,
            interest_rate=base_rate + penalty_premium,
            covenants={
                "dividends_allowed": False,
                "executive_salary_freeze": True,
                "mandatory_repayment": 0.5,
            },
        )

        # The government provides the funds, which become a liability for the firm
        self.government.assets -= amount
        firm.finance.add_liability(amount, loan.interest_rate)

        return loan

    def service_debt(self, current_tick: int) -> None:
        """Manages the servicing of outstanding government debt."""
        # This is a simplified version. A real implementation would handle interest payments
        # and bond maturation.
        matured_bonds = [
            b for b in self.outstanding_bonds if b.maturity_date <= current_tick
        ]
        for bond in matured_bonds:
            self.government.assets -= bond.face_value
            self.outstanding_bonds.remove(bond)
