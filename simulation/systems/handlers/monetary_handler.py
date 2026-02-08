from typing import Any, List, Tuple, Optional
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction, RealEstateUnit
from simulation.firms import Firm
from simulation.core_agents import Household
from simulation.systems.handlers.asset_transfer_handler import AssetTransferHandler

logger = logging.getLogger(__name__)

class MonetaryTransactionHandler(ITransactionHandler):
    """
    Handles monetary policy transactions:
    - lender_of_last_resort (Minting)
    - asset_liquidation (Minting + Asset Transfer)
    - bond_purchase / omo_purchase (Minting / QE)
    - bond_repayment / omo_sale (Burning / QT)
    """

    def __init__(self):
        self.asset_handler = AssetTransferHandler()

    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        tx_type = tx.transaction_type
        trade_value = tx.quantity * tx.price

        # Central Bank is needed for minting/burning
        if not context.central_bank:
            context.logger.error("MonetaryHandler: Central Bank missing in context.")
            return False

        # Central Bank System wrapper usually handles mint/burn but context has central_bank agent.
        # We need to access mint/burn methods if they exist on CentralBank agent or use SettlementSystem helpers.
        # SettlementSystem has 'create_and_transfer' and 'transfer_and_destroy'.

        success = False

        if tx_type == "lender_of_last_resort":
            # Minting: Central Bank (Buyer/Source) -> Bank/Agent (Seller/Target)
            # Typically Buyer is System/Gov/CB. Seller is the one receiving money.
            # TransactionProcessor logic: "success = settlement.transfer(buyer, seller, ...)"
            # Wait, TP used settlement.transfer.
            # If buyer is CentralBank, settlement.transfer should handle minting if it detects CB?
            # SettlementSystem._execute_withdrawal checks if agent is CB and allows infinite withdraw.
            # So simple transfer from CB works for minting.

            success = context.settlement_system.transfer(
                buyer, seller, trade_value, "lender_of_last_resort"
            )
            if success and hasattr(buyer, "total_money_issued"):
                buyer.total_money_issued += trade_value

        elif tx_type == "asset_liquidation":
            # Minting: Gov/CB (Buyer) -> Agent (Seller)
            success = context.settlement_system.transfer(
                buyer, seller, trade_value, "asset_liquidation"
            )
            if success:
                if hasattr(buyer, "total_money_issued"):
                    buyer.total_money_issued += trade_value

                # Asset Transfer Logic (Stock/RE) - Delegated to AssetTransferHandler
                self.asset_handler._apply_asset_effects(tx, buyer, seller, context)

        elif tx_type in ["bond_purchase", "omo_purchase"]:
            # QE: CB (Buyer) -> Gov/Agent (Seller)
            success = context.settlement_system.transfer(
                buyer, seller, trade_value, tx_type
            )
            if success and context.central_bank and buyer.id == context.central_bank.id:
                 if hasattr(context.government, "total_money_issued"):
                     context.government.total_money_issued += trade_value
                 context.logger.info(
                     f"QE | Central Bank purchased bond/asset {trade_value:.2f}.",
                     extra={"tick": context.time, "tag": "QE"}
                 )

        elif tx_type in ["bond_repayment", "omo_sale"]:
            # QT: Agent (Buyer) -> CB (Seller)
            # Burning: Money goes to CB and disappears.
            success = context.settlement_system.transfer(
                buyer, seller, trade_value, tx_type
            )

        return success is not None
