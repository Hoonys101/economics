from typing import Dict, Any, List, Optional
import logging
import uuid
from modules.government.api import IFiscalBondService
from modules.government.dtos import (
    FiscalContextDTO,
    BondIssueRequestDTO,
    BondIssuanceResultDTO,
    PaymentRequestDTO
)
from modules.finance.api import BondDTO
from modules.system.api import DEFAULT_CURRENCY

logger = logging.getLogger(__name__)

class FiscalBondService(IFiscalBondService):
    """
    Stateless service responsible for sovereign debt logic:
    calculating yields, determining buyers (QE), and preparing issuance.
    """

    def __init__(self, config_module: Any = None):
        self.config_module = config_module

    def calculate_yield(self, context: FiscalContextDTO) -> float:
        """
        Calculates bond yield based on market conditions.
        """
        # Base rate should ideally be in context or fetched, but let's assume default or minimal
        # In FinanceSystem it was base_rate + 0.01.
        # We assume base rate is around 3% (0.03).
        base_rate = 0.03

        # Risk premium based on Debt-to-GDP
        # If Debt/GDP > 1.0, add premium.
        risk_premium = 0.0
        if context.debt_to_gdp_ratio > 1.0:
            risk_premium = (context.debt_to_gdp_ratio - 1.0) * 0.02 # 2% per 100% debt over GDP

        return base_rate + risk_premium + 0.01 # +1% base spread

    def issue_bonds(self, request: BondIssueRequestDTO, context: FiscalContextDTO, buyer_pool: Dict[str, Any]) -> BondIssuanceResultDTO:
        """
        Prepares a bond issuance transaction.
        Determines the buyer (e.g. Central Bank vs Commercial Bank) and creates the transaction request.
        """

        # 1. Determine Yield (if not fixed in request)
        yield_rate = request.target_yield
        if yield_rate <= 0:
            yield_rate = self.calculate_yield(context)

        # 2. Determine Buyer (QE Logic)
        qe_threshold = 1.5
        if self.config_module and hasattr(self.config_module, 'get'):
             # Try to get from config if available, otherwise default
             # Assuming config_module is dict-like or object
             if isinstance(self.config_module, dict):
                 qe_threshold = self.config_module.get("economy_params.QE_DEBT_TO_GDP_THRESHOLD", 1.5)
             elif hasattr(self.config_module, "economy_params"):
                 params = getattr(self.config_module, "economy_params", {})
                 if isinstance(params, dict):
                     qe_threshold = params.get("QE_DEBT_TO_GDP_THRESHOLD", 1.5)
             else:
                 # Check flat attributes
                 qe_threshold = getattr(self.config_module, "QE_DEBT_TO_GDP_THRESHOLD", 1.5)

        buyer_id = "UNKNOWN"
        buyer_agent = None

        is_qe = context.debt_to_gdp_ratio > qe_threshold

        if is_qe:
            # Quantitative Easing: Central Bank buys
            if "central_bank" in buyer_pool:
                buyer_agent = buyer_pool["central_bank"]
                if hasattr(buyer_agent, 'id'):
                    buyer_id = buyer_agent.id
                logger.info(f"QE_ACTIVATED | Debt/GDP: {context.debt_to_gdp_ratio:.2f} > {qe_threshold}. Buyer: Central Bank")
            else:
                logger.error("QE required but Central Bank not in buyer pool.")
        else:
            # Normal Operation: Commercial Bank buys
            if "bank" in buyer_pool:
                buyer_agent = buyer_pool["bank"]
                if hasattr(buyer_agent, 'id'):
                    buyer_id = buyer_agent.id
            elif "banks" in buyer_pool and buyer_pool["banks"]:
                 # Pick first bank
                 first_bank = next(iter(buyer_pool["banks"].values()))
                 buyer_agent = first_bank
                 if hasattr(buyer_agent, 'id'):
                     buyer_id = buyer_agent.id

        if not buyer_agent:
             # Fallback
             logger.error("No suitable buyer found for bond issuance.")
             # We still return DTO, but payer might be None/Invalid which Settlement will reject.
             # This allows caller to handle failure gracefully.
             # We generate a dummy request that will likely fail if executed without patching.
             pass

        # 3. Create Bond DTO
        # Generate a unique ID for the bond
        bond_id = f"BOND_{context.tick}_{uuid.uuid4().hex[:8]}"

        maturity_tick = context.tick + request.maturity_ticks

        bond_dto = BondDTO(
            id=bond_id,
            issuer="GOVERNMENT",
            face_value=request.amount_pennies,
            yield_rate=yield_rate,
            maturity_date=maturity_tick
        )

        # 4. Create Payment Request
        # If buyer_agent is None, payer is None. Caller must handle.
        payment_request = PaymentRequestDTO(
            payer=buyer_agent if buyer_agent else "UNKNOWN_BUYER",
            payee="GOVERNMENT",
            amount=request.amount_pennies,
            currency=DEFAULT_CURRENCY,
            memo=f"bond_purchase_{bond_id}"
        )

        return BondIssuanceResultDTO(
            payment_request=payment_request,
            bond_dto=bond_dto
        )
