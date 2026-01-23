import logging
from typing import Optional, Dict, List, Any
from simulation.core_agents import Household
from simulation.agents.government import Government
from simulation.models import Order, Transaction
from simulation.portfolio import Portfolio

logger = logging.getLogger(__name__)

class InheritanceManager:
    """
    Phase 22 (WO-049): Legacy Protocol
    Handles Death, Valuation, Taxation (Liquidation), and Transfer.
    Ensures 'Zero Leak' and atomic settlement.
    """
    def __init__(self, config_module: Any):
        self.config_module = config_module
        self.logger = logging.getLogger("simulation.systems.inheritance_manager")

    def process_death(self, deceased: Household, government: Government, simulation: Any) -> None:
        """
        Executes the inheritance pipeline.

        Args:
            deceased: The agent who died.
            government: The entity collecting tax.
            simulation: Access to markets/registry for liquidation and transfer.
        """
        settlement = getattr(simulation, 'settlement_system', None)
        if not settlement and hasattr(simulation, 'world_state'):
             settlement = getattr(simulation.world_state, 'settlement_system', None)

        self.logger.info(
            f"INHERITANCE_START | Processing death for Household {deceased.id}. Assets: {deceased.assets:.2f}",
            extra={"agent_id": deceased.id, "tags": ["inheritance", "death"]}
        )

        # 1. Valuation
        # ------------------------------------------------------------------
        cash = deceased.assets

        # Real Estate Valuation
        real_estate_value = 0.0
        # Access real estate units from simulation (assuming simulation has list)
        deceased_units = [u for u in simulation.real_estate_units if u.owner_id == deceased.id]

        # We need current market value. Unit.estimated_value should be up to date or we fetch from market?
        # Simulation._process_housing might update estimated_value?
        # Assuming unit.estimated_value is the source of truth for Wealth Tax/Valuation.
        for unit in deceased_units:
            real_estate_value += unit.estimated_value

        # Stock Valuation
        # Portfolio should track quantity. Price from StockMarket.
        stock_value = 0.0
        current_prices = {}
        if simulation.stock_market:
            for firm_id, share in deceased.portfolio.holdings.items():
                price = simulation.stock_market.get_daily_avg_price(firm_id)
                if price <= 0:
                    price = share.acquisition_price # Fallback to book cost
                current_prices[firm_id] = price
                stock_value += share.quantity * price

        total_wealth = cash + real_estate_value + stock_value

        # 2. Taxation
        # ------------------------------------------------------------------
        tax_rate = getattr(self.config_module, "INHERITANCE_TAX_RATE", 0.4)
        deduction = getattr(self.config_module, "INHERITANCE_DEDUCTION", 10000.0)

        taxable_base = max(0.0, total_wealth - deduction)
        tax_amount = taxable_base * tax_rate

        self.logger.info(
            f"ESTATE_VALUATION | Agent {deceased.id}: Cash={cash:.0f}, RE={real_estate_value:.0f}, Stock={stock_value:.0f} -> Total={total_wealth:.0f}. Tax={tax_amount:.0f}",
            extra={"agent_id": deceased.id, "total_wealth": total_wealth, "tax_amount": tax_amount}
        )

        # 3. Liquidation Logic (Atomic)
        # ------------------------------------------------------------------
        # If Cash < Tax, we must liquidate assets instantly to Government.

        # Liquidation Sequence: Stocks -> Real Estate

        # A. Stock Liquidation
        if deceased.assets < tax_amount and stock_value > 0:
            # Sell all stocks to Government/Market Maker at Current Price
            # In WO-049: "Sell Stocks (Market Order)". But for atomic zero-leak, we sim it.
            # Government buys the stocks (providing liquidity).
            # Government doesn't hold stocks usually? Or it burns them?
            # WO says: "Sell Stocks (Market Order)... Sell Real Estate (Fire Sale to Engine/Market)."
            # Implementation: Transfer stocks to Government portfolio? Or just convert to cash (Govt prints money/uses reserves)?
            # Let's assume Government buys them to resolve debt.

            liquidation_proceeds = 0.0

            # To be safe, we sell everything if we are short on cash?
            # Or just enough? Complexity vs speed. "Liquidation" implies selling needed assets.
            # Simple approach: Sell ALL stocks first if cash shortage exists.

            for firm_id, share in list(deceased.portfolio.holdings.items()):
                price = current_prices.get(firm_id, 0.0)
                proceeds = share.quantity * price

                # Transfer: Deceased -> Cash, Government -> Stock (or burn?)
                if settlement:
                    settlement.transfer(government, deceased, proceeds, f"liquidation_stock:{firm_id}")
                else:
                    if hasattr(government, '_sub_assets'): government._sub_assets(proceeds)
                    else: government.assets -= proceeds
                    if hasattr(deceased, '_add_assets'): deceased._add_assets(proceeds)
                    else: deceased.assets += proceeds

                simulation.government.total_money_issued += proceeds # Injection (Bank/Gov Buyout)

                liquidation_proceeds += proceeds

                # Remove from Deceased Portfolio
                deceased.portfolio.remove(firm_id, share.quantity)
                # Sync legacy
                if firm_id in deceased.shares_owned:
                    del deceased.shares_owned[firm_id]

                # Logic gap: Who owns the stock now?
                # If Market Order, random buyer. If Atomic Govt Buyout, Govt owns it.
                # Govt usually sells later? Or holds?
                # For "Legacy Protocol", let's assume Govt holds or burns.
                # Simplest: Burn (Share Buyback equivalent) or Govt holds.
                # Let's update StockMarket registry: Govt owns it.
                if simulation.stock_market:
                    simulation.stock_market.update_shareholder(deceased.id, firm_id, 0)
                    # Update Govt
                    # simulation.stock_market.update_shareholder(government.id, firm_id, ...?)
                    # Not strictly required unless Govt trades.

            self.logger.info(
                f"LIQUIDATION_STOCK | Sold stocks for {liquidation_proceeds:.2f} to cover tax.",
                 extra={"agent_id": deceased.id}
            )

        # B. Real Estate Liquidation (Fire Sale)
        if deceased.assets < tax_amount:
            # Still short? Sell Properties.
            # Fire Sale @ 90%
            fire_sale_ratio = 0.9

            for unit in deceased_units:
                if deceased.assets >= tax_amount:
                    break # Stop if we have enough cash

                sale_price = unit.estimated_value * fire_sale_ratio

                # Govt buys unit
                if settlement:
                    settlement.transfer(government, deceased, sale_price, f"liquidation_re:{unit.id}")
                else:
                    if hasattr(government, '_sub_assets'): government._sub_assets(sale_price)
                    else: government.assets -= sale_price
                    if hasattr(deceased, '_add_assets'): deceased._add_assets(sale_price)
                    else: deceased.assets += sale_price

                simulation.government.total_money_issued += sale_price # Injection

                # Transfer Title
                unit.owner_id = None # Government/Public
                # Or set to Government ID?
                # Simulation uses None for Government owned.

                # Remove from Deceased list
                deceased.owned_properties.remove(unit.id)

                self.logger.info(
                    f"LIQUIDATION_RE | Sold Unit {unit.id} for {sale_price:.2f} (Fire Sale).",
                    extra={"agent_id": deceased.id, "unit_id": unit.id}
                )

        # 4. Tax Payment
        # ------------------------------------------------------------------
        # Determine final tax payment (limited by assets if bankruptcy)
        actual_tax_paid = min(deceased.assets, tax_amount)
        if actual_tax_paid > 0:
            if settlement:
                settlement.transfer(deceased, government, actual_tax_paid, "inheritance_tax")
            else:
                deceased.withdraw(actual_tax_paid)
                government.deposit(actual_tax_paid)

            simulation.government.collect_tax(actual_tax_paid, "inheritance_tax", deceased, simulation.time)

        # 5. Distribution (Transfer)
        # ------------------------------------------------------------------
        # Find Heirs
        heirs = []
        for child_id in deceased.children_ids:
            child = simulation.agents.get(child_id)
            if child and child.is_active:
                heirs.append(child)

        if not heirs:
            # 1. State Confiscation (Cash)
            surplus = deceased.assets
            if surplus > 0:
                if settlement:
                    settlement.transfer(deceased, government, surplus, "escheatment_no_heirs")
                else:
                    deceased.withdraw(surplus)
                    government.deposit(surplus)

                simulation.government.collect_tax(surplus, "escheatment", deceased, simulation.time)
                self.logger.info(
                    f"NO_HEIRS | Confiscated cash {surplus:.2f} to Government.",
                    extra={"agent_id": deceased.id}
                )

            # 2. State Confiscation (Stocks)
            # Transfer all remaining shares to Government
            for firm_id, share in list(deceased.portfolio.holdings.items()):
                 qty = share.quantity
                 if qty > 0:
                     # Update Shareholder Registry: Deceased -> 0, Govt -> +qty
                     if simulation.stock_market:
                         simulation.stock_market.update_shareholder(deceased.id, firm_id, 0)
                         simulation.stock_market.update_shareholder(simulation.government.id, firm_id, qty)
            
            # Clear Deceased Portfolio
            deceased.portfolio.holdings.clear()
            deceased.shares_owned.clear()

            # 3. State Confiscation (Real Estate)
            # Transfer all remaining properties to Government
            remaining_units = [u for u in simulation.real_estate_units if u.owner_id == deceased.id]
            for unit in remaining_units:
                unit.owner_id = simulation.government.id
                # Note: deceased.owned_properties will be cleared below
            
            deceased.owned_properties.clear()
            
            self.logger.info(
                 f"NO_HEIRS_ASSETS | Confiscated {len(remaining_units)} properties and portfolio to Government.",
                 extra={"agent_id": deceased.id}
            )

            return

        # Split Remaining Assets
        num_heirs = len(heirs)

        # A. Cash
        total_cash = deceased.assets
        cash_share = round(total_cash / num_heirs, 2)
        total_distributed = 0.0

        for heir in heirs:
            if settlement:
                settlement.transfer(deceased, heir, cash_share, f"inheritance_share:{deceased.id}")
            else:
                deceased._sub_assets(cash_share)
                heir._add_assets(cash_share)
            total_distributed += cash_share

        # Residual Catch-all (WO-112)
        # Note: If deceased.assets was reduced by transfer, we check remainder via calculation or checking asset balance.
        # Since we used settlement (which reduces asset), deceased.assets should be ~0.
        # But cash_share logic used deceased.assets (initial) / num_heirs.
        # The remainder is mathematically (Total - (Share * N)).
        # If we transferred (Share * N), the deceased might have a small remaining balance due to rounding.
        # Let's check remaining balance.

        remainder = deceased.assets
        if remainder > 0:
             if settlement:
                 settlement.transfer(deceased, government, remainder, "inheritance_residual")
             else:
                 deceased.withdraw(remainder)
                 government.deposit(remainder)

             simulation.government.collect_tax(remainder, "inheritance_residual", deceased, simulation.time)
             self.logger.info(f"RESIDUAL_CAPTURED | Transferred {remainder:.4f} residual dust to Government.")

        # deceased.assets should be 0.0 now.

        # B. Stocks (Portfolio Merge)
        # Split each holding N ways
        for firm_id, share in list(deceased.portfolio.holdings.items()):
            qty_per_heir = share.quantity / num_heirs
            if qty_per_heir > 0:
                for heir in heirs:
                    heir.portfolio.add(firm_id, qty_per_heir, share.acquisition_price)
                    # Legacy Sync
                    current_legacy = heir.shares_owned.get(firm_id, 0.0)
                    heir.shares_owned[firm_id] = current_legacy + qty_per_heir

                    if simulation.stock_market:
                         simulation.stock_market.update_shareholder(heir.id, firm_id, heir.shares_owned[firm_id])

            # Clear deceased
            if simulation.stock_market:
                simulation.stock_market.update_shareholder(deceased.id, firm_id, 0)

        deceased.portfolio.holdings.clear()
        deceased.shares_owned.clear()

        # C. Real Estate
        # Split properties? Impossible to split 1 unit.
        # Logic: Assign units round-robin to heirs? Or sell and split cash?
        # WO says "RealEstate: Update Registry Owner ID." implying transfer.
        # Simple Round Robin.
        remaining_units = [u for u in simulation.real_estate_units if u.owner_id == deceased.id]

        for i, unit in enumerate(remaining_units):
            target_heir = heirs[i % num_heirs]

            unit.owner_id = target_heir.id
            if hasattr(target_heir, 'owned_properties'):
                target_heir.owned_properties.append(unit.id)
            # Deceased removed locally from list (we iterate copy or access simulation list)
            # deceased.owned_properties already handled? No.
            # We iterate `remaining_units` which is fresh list.

        deceased.owned_properties.clear()

        self.logger.info(
            f"INHERITANCE_COMPLETE | Transferred assets to {num_heirs} heirs.",
            extra={"agent_id": deceased.id, "heirs_count": num_heirs}
        )
