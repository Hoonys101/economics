from typing import Any, List, Tuple, Optional
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction, RealEstateUnit
from simulation.firms import Firm
from simulation.core_agents import Household
from modules.common.interfaces import IInvestor, IPropertyOwner

logger = logging.getLogger(__name__)

class MonetaryTransactionHandler(ITransactionHandler):
    """
    Handles monetary policy transactions:
    - lender_of_last_resort (Minting)
    - asset_liquidation (Minting + Asset Transfer)
    - bond_purchase / omo_purchase (Minting / QE)
    - bond_repayment / omo_sale (Burning / QT)
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        tx_type = tx.transaction_type
        trade_value = tx.total_pennies

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
                buyer, seller, int(trade_value), "lender_of_last_resort"
            )
            if success and hasattr(buyer, "total_money_issued"):
                buyer.total_money_issued += trade_value

        elif tx_type == "asset_liquidation":
            # Minting: Gov/CB (Buyer) -> Agent (Seller)
            success = context.settlement_system.transfer(
                buyer, seller, int(trade_value), "asset_liquidation"
            )
            if success:
                if hasattr(buyer, "total_money_issued"):
                    buyer.total_money_issued += trade_value

                # Asset Transfer Logic (Stock/RE)
                self._apply_asset_liquidation_effects(tx, buyer, seller, context)

        elif tx_type == "bond_interest":
             success = context.settlement_system.transfer(
                 buyer, seller, int(trade_value), tx_type
             )

        elif tx_type in ["bond_purchase", "omo_purchase"]:
            # QE: CB (Buyer) -> Gov/Agent (Seller)
            success = context.settlement_system.transfer(
                buyer, seller, int(trade_value), tx_type
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
                buyer, seller, int(trade_value), tx_type
            )
            if success and context.central_bank and seller.id == context.central_bank.id:
                if hasattr(context.government, "total_money_destroyed"):
                    context.government.total_money_destroyed += trade_value
                context.logger.info(
                    f"QT | Central Bank sold bond/asset {trade_value:.2f}.",
                    extra={"tick": context.time, "tag": "QT"}
                )

        return success is not None

    def _apply_asset_liquidation_effects(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext):
        """
        Handles asset transfer side-effects for liquidation.
        """
        if tx.item_id.startswith("stock_"):
            self._handle_stock_side_effect(tx, buyer, seller, context)
        elif tx.item_id.startswith("real_estate_"):
            self._handle_real_estate_side_effect(tx, buyer, seller, context)

    def _handle_stock_side_effect(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext):
        try:
            firm_id = int(tx.item_id.split("_")[1])
        except (IndexError, ValueError):
            return

        # 1. Seller Holdings
        if isinstance(seller, IInvestor):
            seller.portfolio.remove(firm_id, tx.quantity)
        elif isinstance(seller, Household) and hasattr(seller, "shares_owned"):
             # Legacy Fallback
            current_shares = seller.shares_owned.get(firm_id, 0)
            seller.shares_owned[firm_id] = max(0, current_shares - tx.quantity)
            if seller.shares_owned[firm_id] <= 0 and firm_id in seller.shares_owned:
                del seller.shares_owned[firm_id]
        elif isinstance(seller, Firm) and seller.id == firm_id:
            seller.treasury_shares = max(0, seller.treasury_shares - tx.quantity)

        # 2. Buyer Holdings
        if isinstance(buyer, IInvestor):
            price_pennies = int(tx.total_pennies / tx.quantity) if tx.quantity > 0 else 0
            buyer.portfolio.add(firm_id, tx.quantity, price_pennies)
        elif isinstance(buyer, Household) and hasattr(buyer, "shares_owned"):
            # Legacy Fallback
            buyer.shares_owned[firm_id] = buyer.shares_owned.get(firm_id, 0) + tx.quantity
        elif isinstance(buyer, Firm) and buyer.id == firm_id:
            buyer.treasury_shares += tx.quantity
            buyer.total_shares -= tx.quantity

        # 3. Market Registry
        if context.stock_market:
            if isinstance(buyer, IInvestor) and firm_id in buyer.portfolio.holdings:
                 context.stock_market.update_shareholder(buyer.id, firm_id, buyer.portfolio.holdings[firm_id].quantity)
            if isinstance(seller, IInvestor) and firm_id in seller.portfolio.holdings:
                context.stock_market.update_shareholder(seller.id, firm_id, seller.portfolio.holdings[firm_id].quantity)
            else:
                context.stock_market.update_shareholder(seller.id, firm_id, 0.0)

    def _handle_real_estate_side_effect(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext):
        try:
            unit_id_str = tx.item_id.split("_")[2]
            unit_id = int(unit_id_str)
            unit = next((u for u in context.real_estate_units if u.id == unit_id), None)

            if unit:
                unit.owner_id = buyer.id
                if isinstance(seller, IPropertyOwner) and unit_id in seller.owned_properties:
                    seller.remove_property(unit_id)
                if isinstance(buyer, IPropertyOwner):
                    buyer.add_property(unit_id)
        except (IndexError, ValueError):
            pass
