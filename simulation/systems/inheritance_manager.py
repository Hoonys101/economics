import logging
import math
from typing import Optional, Dict, List, Any, TYPE_CHECKING
from simulation.core_agents import Household
from simulation.agents.government import Government
from simulation.models import Order, Transaction
from simulation.portfolio import Portfolio
from modules.system.api import DEFAULT_CURRENCY
from modules.system.constants import ID_SYSTEM
from modules.finance.utils.currency_math import round_to_pennies

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState

class InheritanceManager:
    """
    Phase 22 (WO-049): Legacy Protocol
    Handles Death, Valuation, Taxation (Liquidation), and Transfer.
    Ensures 'Zero Leak' and atomic settlement via SettlementSystem.
    """
    def __init__(self, config_module: Any):
        self.config_module = config_module
        self.logger = logging.getLogger("simulation.systems.inheritance_manager")

    def _get_agent_balance_pennies(self, agent: Household) -> int:
        """Helper to get balance in integer pennies."""
        # Check if DTO or Entity
        if hasattr(agent, "balance_pennies"):
            return agent.balance_pennies

        # Access assets directly (legacy float)
        # Handle dict or float
        raw = agent._econ_state.assets
        if isinstance(raw, dict):
            raw = raw.get(DEFAULT_CURRENCY, 0.0)

        # Use round_to_pennies for safety against float representation errors
        return round_to_pennies(raw * 100)

    def _wipe_agent_assets(self, agent: Household) -> None:
        """Explicitly zero out agent assets to prevent floating point leaks."""
        if isinstance(agent._econ_state.assets, dict):
            agent._econ_state.assets[DEFAULT_CURRENCY] = 0.0
        else:
            agent._econ_state.assets = 0.0

    def process_death(self, deceased: Household, government: Government, simulation: "SimulationState") -> List[Transaction]:
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

        # 1. Valuation & Asset Gathering
        # ------------------------------------------------------------------
        # Work with integer pennies for cash operations
        cash_pennies = self._get_agent_balance_pennies(deceased)

        self.logger.info(
            f"INHERITANCE_START | Processing death for Household {deceased.id}. Assets (Pennies): {cash_pennies}",
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

        # Total wealth for TAX calculation (can use float logic for valuation)
        cash_float = cash_pennies / 100.0
        total_wealth = round(cash_float + real_estate_value + stock_value, 2)

        # 2. Liquidation for Tax (if needed)
        # ------------------------------------------------------------------
        tax_rate = getattr(self.config_module, "INHERITANCE_TAX_RATE", 0.4)
        deduction = getattr(self.config_module, "INHERITANCE_DEDUCTION", 10000.0)
        taxable_base = max(0.0, total_wealth - deduction)

        # Calculate Tax in Pennies
        tax_amount_float = round(taxable_base * tax_rate, 2)
        tax_pennies = round_to_pennies(tax_amount_float * 100)

        if cash_pennies < tax_pennies:
            # Need to liquidate assets to pay tax.
            needed_pennies = tax_pennies - cash_pennies

            # A. Stock Liquidation
            if needed_pennies > 0 and stock_value > 0:
                for firm_id, share in list(portfolio_holdings.items()):
                    price = current_prices.get(firm_id, 0.0)
                    proceeds = round(share.quantity * price, 2)
                    proceeds_pennies = round_to_pennies(proceeds * 100)

                    # TD-232: Use TransactionProcessor for atomic execution + side effects
                    tx = Transaction(
                        buyer_id=government.id,
                        seller_id=deceased.id,
                        item_id=f"stock_{firm_id}",
                        quantity=share.quantity,
                        price=price,
                        total_pennies=proceeds_pennies,
                        market_id="stock_market",
                        transaction_type="asset_liquidation",
                        time=current_tick,
                        metadata={"executed": False}
                    )

                    results = simulation.transaction_processor.execute(simulation, [tx])

                    if results and results[0].success:
                        # Success - proceeds have been transferred and assets moved by Handler
                        if firm_id in portfolio_holdings:
                             del portfolio_holdings[firm_id] # Keep local copy in sync

                        # Mark as executed for reporting
                        tx.metadata["executed"] = True
                        transactions.append(tx)

                        cash_pennies += proceeds_pennies
                        needed_pennies -= proceeds_pennies
                        if needed_pennies <= 0:
                            break

            # B. Real Estate Liquidation
            if needed_pennies > 0 and real_estate_value > 0:
                fire_sale_ratio = 0.9
                for unit in list(deceased_units):
                    sale_price = round(unit.estimated_value * fire_sale_ratio, 2)
                    sale_price_pennies = round_to_pennies(sale_price * 100)

                    # TD-232: Use TransactionProcessor
                    tx = Transaction(
                        buyer_id=government.id,
                        seller_id=deceased.id,
                        item_id=f"real_estate_{unit.id}",
                        quantity=1.0,
                        price=sale_price,
                        total_pennies=sale_price_pennies,
                        market_id="real_estate_market",
                        transaction_type="asset_liquidation",
                        time=current_tick,
                        metadata={"executed": False}
                    )

                    results = simulation.transaction_processor.execute(simulation, [tx])

                    if results and results[0].success:
                        deceased_units.remove(unit)
                        tx.metadata["executed"] = True
                        transactions.append(tx)

                        cash_pennies += sale_price_pennies
                        needed_pennies -= sale_price_pennies
                        if needed_pennies <= 0:
                            break

        # 4. Plan Distribution & Execution
        # ------------------------------------------------------------------

        # A. Tax
        tax_to_pay_pennies = min(cash_pennies, tax_pennies)
        if tax_to_pay_pennies > 0:
            tx = Transaction(
                buyer_id=deceased.id, # Payer
                seller_id=government.id, # Payee
                item_id="inheritance_tax",
                quantity=1.0,
                price=tax_to_pay_pennies / 100.0,
                total_pennies=tax_to_pay_pennies,
                market_id="system",
                transaction_type="tax",
                time=current_tick
            )
            results = simulation.transaction_processor.execute(simulation, [tx])
            if results and results[0].success:
                transactions.append(tx)
                cash_pennies -= tax_to_pay_pennies

        # B. Heirs & Escheatment
        heirs = []
        for child_id in deceased._bio_state.children_ids:
            child = simulation.agents.get(child_id)
            if child and child._bio_state.is_active:
                heirs.append(child)

        if not heirs:
            # Escheatment (To Gov)
            if cash_pennies > 0:
                # TD-232: Escheatment via TransactionProcessor
                # Note: EscheatmentHandler transfers ALL assets.
                # Since we already paid tax, remaining cash is escheated.
                tx = Transaction(
                    buyer_id=deceased.id,
                    seller_id=government.id,
                    item_id="escheatment",
                    quantity=1.0,
                    price=cash_pennies / 100.0, # Used for record, handler takes all
                    total_pennies=cash_pennies,
                    market_id="system",
                    transaction_type="escheatment",
                    time=current_tick
                )
                results = simulation.transaction_processor.execute(simulation, [tx])
                if results and results[0].success:
                    transactions.append(tx)
                    # cash_pennies should be 0 now conceptually

            # Escheat remaining Real Estate (Execute Synchronously)
            for unit in deceased_units:
                 tx = Transaction(
                        buyer_id=government.id,
                        seller_id=deceased.id,
                        item_id=f"real_estate_{unit.id}",
                        quantity=1.0,
                        price=0.0,
                        total_pennies=0,
                        market_id="real_estate_market",
                        transaction_type="asset_transfer",
                        time=current_tick,
                        metadata={"executed": False}
                     )

                 results = simulation.transaction_processor.execute(simulation, [tx])
                 if results and results[0].success:
                     tx.metadata["executed"] = True
                     transactions.append(tx)

        else:
            # Distribute to Heirs
            # Cash & Portfolio via InheritanceHandler (Single Transaction)
            if cash_pennies > 0:
                tx = Transaction(
                    buyer_id=deceased.id,
                    seller_id=ID_SYSTEM, # System distribution (Fixed COLLISION with PublicManager -1)
                    item_id="estate_distribution",
                    quantity=1.0,
                    price=cash_pennies / 100.0, # Informational
                    total_pennies=cash_pennies,
                    market_id="system",
                    transaction_type="inheritance_distribution",
                    time=current_tick,
                    metadata={"heir_ids": [h.id for h in heirs]}
                )
                results = simulation.transaction_processor.execute(simulation, [tx])
                if results and results[0].success:
                    transactions.append(tx)

            # Distribute Real Estate (Round Robin - Synchronous)
            count = len(heirs)
            for i, unit in enumerate(deceased_units):
                recipient = heirs[i % count]

                tx = Transaction(
                        buyer_id=recipient.id,
                        seller_id=deceased.id,
                        item_id=f"real_estate_{unit.id}",
                        quantity=1.0,
                        price=0.0,
                        total_pennies=0,
                        market_id="real_estate_market",
                        transaction_type="asset_transfer",
                        time=current_tick,
                        metadata={"executed": False}
                     )

                results = simulation.transaction_processor.execute(simulation, [tx])
                if results and results[0].success:
                    tx.metadata["executed"] = True
                    transactions.append(tx)

        # 5. Dust Cleanup
        # Explicitly zero out assets to prevent floating point leaks
        self._wipe_agent_assets(deceased)

        return transactions

    def _dict_to_transaction(self, tx_dict: dict) -> Transaction:
         # Deprecated but kept if needed by other methods not shown
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
