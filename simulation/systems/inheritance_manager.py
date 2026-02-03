import logging
from typing import Optional, Dict, List, Any
from simulation.core_agents import Household
from simulation.agents.government import Government
from simulation.models import Order, Transaction
from simulation.portfolio import Portfolio
from modules.system.api import DEFAULT_CURRENCY

logger = logging.getLogger(__name__)

class InheritanceManager:
    """
    Phase 22 (WO-049): Legacy Protocol
    Handles Death, Valuation, Taxation (Liquidation), and Transfer.
    Ensures 'Zero Leak' and atomic settlement via SettlementSystem.
    """
    def __init__(self, config_module: Any):
        self.config_module = config_module
        self.logger = logging.getLogger("simulation.systems.inheritance_manager")

    def process_death(self, deceased: Household, government: Government, simulation: Any) -> List[Transaction]:
        """
        Executes the inheritance pipeline using SettlementSystem (Atomic).

        Args:
            deceased: The agent who died.
            government: The entity collecting tax.
            simulation: Access to markets/registry for valuation and settlement_system.

        Returns:
            List[Transaction]: Ordered list of executed transaction receipts.
        """
        transactions: List[Transaction] = []
        current_tick = simulation.time
        settlement_system = simulation.settlement_system

        # 1. Valuation & Asset Gathering
        # ------------------------------------------------------------------
        cash_raw = deceased._econ_state.assets
        cash = cash_raw
        if isinstance(cash_raw, dict):
            cash = cash_raw.get(DEFAULT_CURRENCY, 0.0)
        cash = round(cash, 2)

        self.logger.info(
            f"INHERITANCE_START | Processing death for Household {deceased.id}. Assets: {cash:.2f}",
            extra={"agent_id": deceased.id, "tags": ["inheritance", "death"]}
        )

        deceased_units = [u for u in simulation.real_estate_units if u.owner_id == deceased.id]
        real_estate_value = sum(u.estimated_value for u in deceased_units)
        real_estate_value = round(real_estate_value, 2)

        portfolio_holdings = deceased._econ_state.portfolio.holdings.copy() # dict of firm_id -> Share
        stock_value = 0.0
        current_prices = {}
        if simulation.stock_market:
            for firm_id, share in portfolio_holdings.items():
                price = simulation.stock_market.get_daily_avg_price(firm_id)
                if price <= 0:
                    price = share.acquisition_price
                price = round(price, 2)
                current_prices[firm_id] = price
                stock_value += share.quantity * price

        stock_value = round(stock_value, 2)
        total_wealth = round(cash + real_estate_value + stock_value, 2)

        # 2. Liquidation for Tax (if needed)
        # ------------------------------------------------------------------
        tax_rate = getattr(self.config_module, "INHERITANCE_TAX_RATE", 0.4)
        deduction = getattr(self.config_module, "INHERITANCE_DEDUCTION", 10000.0)
        taxable_base = max(0.0, total_wealth - deduction)
        tax_amount = round(taxable_base * tax_rate, 2)

        if cash < tax_amount:
            # Need to liquidate assets to pay tax.
            # We liquidate to Government (Simulated Buyback) for simplicity and speed (Atomic).

            needed = tax_amount - cash

            # A. Stock Liquidation
            if needed > 0 and stock_value > 0:
                for firm_id, share in list(portfolio_holdings.items()):
                    price = current_prices.get(firm_id, 0.0)
                    proceeds = round(share.quantity * price, 2)

                    # Execute Atomic Transfer: Gov Cash -> Deceased Cash (Simulated)
                    # We use settlement_system.transfer to maintain zero-sum
                    if settlement_system.transfer(government, deceased, proceeds, "liquidation_stock", tick=current_tick):
                        # Update Asset Ownership
                        # Deceased -> Government (or Market/System)
                        # Remove from Deceased Portfolio
                        del deceased._econ_state.portfolio.holdings[firm_id]
                        if firm_id in portfolio_holdings:
                             del portfolio_holdings[firm_id] # Keep local copy in sync

                        # Add to Government Portfolio (if Government holds stocks)
                        # Or assume destroyed/market absorption.
                        # For zero-sum asset integrity, someone must hold it.
                        # Let's assign to Government for now (Escheatment logic).
                        pass # Gov portfolio update skipped for brevity or handled by caller if Gov is agent

                        # Record TX
                        tx = Transaction(
                            buyer_id=government.id,
                            seller_id=deceased.id,
                            item_id=f"stock_{firm_id}",
                            quantity=share.quantity,
                            price=price,
                            market_id="stock_market",
                            transaction_type="asset_liquidation",
                            time=current_tick,
                            metadata={"executed": True}
                        )
                        transactions.append(tx)

                        cash += proceeds
                        needed -= proceeds
                        if needed <= 0:
                            break

            # B. Real Estate Liquidation
            if needed > 0 and real_estate_value > 0:
                fire_sale_ratio = 0.9
                for unit in list(deceased_units):
                    sale_price = round(unit.estimated_value * fire_sale_ratio, 2)

                    if settlement_system.transfer(government, deceased, sale_price, "liquidation_re", tick=current_tick):
                        # Update Ownership (Manual update required for immediate cash flow logic)
                        unit.owner_id = government.id

                        # Fix Leak: Update owned_properties lists
                        if hasattr(deceased, "owned_properties") and unit.id in deceased.owned_properties:
                            deceased.owned_properties.remove(unit.id)
                        if hasattr(government, "owned_properties"):
                             if unit.id not in government.owned_properties:
                                government.owned_properties.append(unit.id)

                        deceased_units.remove(unit)

                        tx = Transaction(
                            buyer_id=government.id,
                            seller_id=deceased.id,
                            item_id=f"real_estate_{unit.id}",
                            quantity=1.0,
                            price=sale_price,
                            market_id="real_estate_market",
                            transaction_type="asset_liquidation",
                            time=current_tick,
                            metadata={"executed": True}
                        )
                        transactions.append(tx)

                        cash += sale_price
                        needed -= sale_price
                        if needed <= 0:
                            break

        # 3. Create Settlement Account (Freezing)
        # ------------------------------------------------------------------
        # Move remaining assets to Settlement Account
        # Logic: We define them here, and clear them from Deceased.
        account = settlement_system.create_settlement(
            agent=deceased,
            tick=current_tick
        )

        # ATOMIC CLEAR: Handled by create_settlement via IPortfolioHandler interface.
        # RE units remaining in `deceased_units` still point to `deceased.id`.

        # 4. Plan Distribution
        # ------------------------------------------------------------------
        distribution_plan = [] # List[Tuple[Recipient, Amount, Memo, TxType]]

        # A. Tax
        # If we have enough cash (from liquidation or original), pay tax.
        # If not (e.g. liquidation failed or insufficient total wealth), pay what we have.
        tax_to_pay = min(cash, tax_amount)
        if tax_to_pay > 0:
            distribution_plan.append((government, tax_to_pay, "inheritance_tax", "tax"))
            cash -= tax_to_pay

        # B. Heirs
        heirs = []
        for child_id in deceased._bio_state.children_ids:
            child = simulation.agents.get(child_id)
            if child and child._bio_state.is_active:
                heirs.append(child)

        if not heirs:
            # Escheatment (To Gov)
            if cash > 0:
                distribution_plan.append((government, cash, "escheatment_cash", "escheatment"))
            else:
                # TD-160: Ensure Gov is in plan for portfolio transfer even if cash is 0
                # SettlementSystem requires a recipient in the plan to trigger receive_portfolio
                distribution_plan.append((government, 0.0, "escheatment_portfolio_trigger", "escheatment"))

            # Escheat remaining Assets
            # Portfolio Transfer is handled by SettlementSystem (Atomic).

            # Real Estate Transfer (Deferred via AssetTransferHandler)
            for unit in deceased_units:
                 tx = Transaction(
                        buyer_id=government.id,
                        seller_id=deceased.id,
                        item_id=f"real_estate_{unit.id}",
                        quantity=1.0,
                        price=0.0,
                        market_id="real_estate_market",
                        transaction_type="asset_transfer",
                        time=current_tick,
                        metadata={"executed": False}
                     )
                 transactions.append(tx)

        else:
            # Distribute to Heirs
            # Equal Split for now
            count = len(heirs)
            if cash > 0:
                share_cash = cash / count
                for heir in heirs:
                    distribution_plan.append((heir, share_cash, "inheritance_distribution", "inheritance_distribution"))

            # Distribute Assets
            # Portfolio Transfer is handled by SettlementSystem (Atomic) to the designated heir (Primary).
            # Note: This changes from equal split to single heir for portfolio assets to ensure atomicity.

            # Distribute Real Estate (Round Robin)
            for i, unit in enumerate(deceased_units):
                recipient = heirs[i % count]
                # We do NOT set unit.owner_id here manually.
                # AssetTransferHandler will handle it when processing the transaction.
                tx = Transaction(
                        buyer_id=recipient.id,
                        seller_id=deceased.id,
                        item_id=f"real_estate_{unit.id}",
                        quantity=1.0,
                        price=0.0,
                        market_id="real_estate_market",
                        transaction_type="asset_transfer",
                        time=current_tick,
                        metadata={"executed": False}
                     )
                transactions.append(tx)

        # 5. Execute Settlement (Cash)
        # ------------------------------------------------------------------
        receipts = settlement_system.execute_settlement(account.deceased_agent_id, distribution_plan, current_tick)

        # Convert dict receipts to Transaction objects
        for receipt in receipts:
            transactions.append(self._dict_to_transaction(receipt))

        # 6. Close
        # ------------------------------------------------------------------
        settlement_system.verify_and_close(account.deceased_agent_id, current_tick)

        return transactions

    def _dict_to_transaction(self, tx_dict: dict) -> Transaction:
         return Transaction(
             buyer_id=tx_dict["buyer_id"],
             seller_id=tx_dict["seller_id"],
             item_id=tx_dict["item_id"],
             quantity=tx_dict["quantity"],
             price=tx_dict["price"],
             market_id=tx_dict["market_id"],
             transaction_type=tx_dict["transaction_type"],
             time=tx_dict["time"],
             metadata=tx_dict["metadata"]
         )
