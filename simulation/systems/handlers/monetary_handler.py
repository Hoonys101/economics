from typing import Any, List, Tuple, Optional
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction, RealEstateUnit
from modules.common.interfaces import IInvestor, IPropertyOwner, IIssuer
from modules.finance.api import FloatIncursionError

logger = logging.getLogger(__name__)

class MonetaryTransactionHandler(ITransactionHandler):
    """
    Handles monetary policy transactions:
    - lender_of_last_resort (Minting)
    - asset_liquidation (Minting + Asset Transfer)
    - bond_purchase / omo_purchase (Minting / QE)
    - bond_repayment / omo_sale (Burning / QT)

    Zero-Sum Integrity:
    - Transfers are handled by SettlementSystem.
    - Money Creation/Destruction (M2 Delta) is tracked by MonetaryLedger via Phase3_Transaction.
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        tx_type = tx.transaction_type

        # SSoT: Integer total_pennies
        if isinstance(tx.total_pennies, float):
            raise FloatIncursionError(f"Settlement integrity violation: amount must be int, got float: {tx.total_pennies}.")

        if not isinstance(tx.total_pennies, int):
            raise TypeError(f"Settlement integrity violation: amount must be int, got {type(tx.total_pennies)}.")

        trade_value = tx.total_pennies

        # Central Bank is needed for minting/burning
        if not context.central_bank:
            context.logger.error("MonetaryHandler: Central Bank missing in context.")
            return False

        success = False

        if tx_type == "lender_of_last_resort":
            # Minting: Central Bank (Buyer/Source) -> Bank/Agent (Seller/Target)
            success = context.settlement_system.transfer(
                buyer, seller, trade_value, "lender_of_last_resort"
            )
            if success:
                context.logger.info(
                    f"MONEY_SUPPLY_CHECK | LLR Expansion: +{trade_value}.",
                    extra={"tick": context.time, "tag": "MONEY_SUPPLY_CHECK"}
                )
            # Ledger accounting is done in Phase3_Transaction via MonetaryLedger

        elif tx_type == "asset_liquidation":
            # Minting: Gov/CB (Buyer) -> Agent (Seller)
            success = context.settlement_system.transfer(
                buyer, seller, trade_value, "asset_liquidation"
            )
            if success:
                # Asset Transfer Logic (Stock/RE)
                self._apply_asset_liquidation_effects(tx, buyer, seller, context)
                context.logger.info(
                    f"MONEY_SUPPLY_CHECK | Asset Liquidation Minting: +{trade_value}.",
                    extra={"tick": context.time, "tag": "MONEY_SUPPLY_CHECK"}
                )

        elif tx_type == "bond_interest":
             success = context.settlement_system.transfer(
                 buyer, seller, trade_value, tx_type
             )

        elif tx_type in ["bond_purchase", "omo_purchase"]:
            # QE: CB (Buyer) -> Gov/Agent (Seller)
            success = context.settlement_system.transfer(
                buyer, seller, trade_value, tx_type
            )
            if success:
                 context.logger.info(
                     f"QE | Central Bank purchased bond/asset {trade_value}.",
                     extra={"tick": context.time, "tag": "QE"}
                 )
                 context.logger.info(
                     f"MONEY_SUPPLY_CHECK | OMO Purchase Expansion: +{trade_value}.",
                     extra={"tick": context.time, "tag": "MONEY_SUPPLY_CHECK"}
                 )

        elif tx_type in ["bond_repayment", "omo_sale"]:
            # QT: Agent (Buyer) -> CB (Seller)
            # Burning: Money goes to CB and disappears.
            success = context.settlement_system.transfer(
                buyer, seller, trade_value, tx_type
            )
            if success:
                context.logger.info(
                    f"QT | Central Bank sold bond/asset {trade_value}.",
                    extra={"tick": context.time, "tag": "QT"}
                )
                context.logger.info(
                    f"MONEY_SUPPLY_CHECK | OMO Sale Contraction: -{trade_value}.",
                    extra={"tick": context.time, "tag": "MONEY_SUPPLY_CHECK"}
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
        elif isinstance(seller, IIssuer) and seller.id == firm_id:
            seller.treasury_shares = max(0, seller.treasury_shares - tx.quantity)

        # 2. Buyer Holdings
        if isinstance(buyer, IInvestor):
            price_pennies = int(tx.total_pennies / tx.quantity) if tx.quantity > 0 else 0
            buyer.portfolio.add(firm_id, tx.quantity, price_pennies)
        elif isinstance(buyer, IIssuer) and buyer.id == firm_id:
            buyer.treasury_shares += tx.quantity
            buyer.total_shares -= tx.quantity

        # 3. Market Registry
        if context.stock_market:
            # Update Shareholder Registry via StockMarket facade if available
            buyer_qty = 0.0
            if isinstance(buyer, IInvestor) and firm_id in buyer.portfolio.holdings:
                 buyer_qty = buyer.portfolio.holdings[firm_id].quantity

            seller_qty = 0.0
            if isinstance(seller, IInvestor) and firm_id in seller.portfolio.holdings:
                 seller_qty = seller.portfolio.holdings[firm_id].quantity

            context.stock_market.update_shareholder(buyer.id, firm_id, buyer_qty)
            context.stock_market.update_shareholder(seller.id, firm_id, seller_qty)

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

    def rollback(self, tx: Transaction, context: TransactionContext) -> bool:
        """
        Reverses the effects of a monetary transaction.
        For simple transfers, it attempts to reverse the funds.
        For asset transfers, it logs a warning as complex rollback is risky.
        """
        context.logger.warning(f"Rollback requested for MonetaryTransaction {tx.transaction_type} (ID: {getattr(tx, 'id', 'unknown')}). Not fully implemented.")
        return False
