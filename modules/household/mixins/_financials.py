from __future__ import annotations
from typing import List, Dict, Optional, Any, TYPE_CHECKING, override
from logging import Logger

from modules.system.api import DEFAULT_CURRENCY, CurrencyCode
from modules.finance.api import PortfolioDTO, PortfolioAsset
from simulation.models import Order
from simulation.portfolio import Portfolio

if TYPE_CHECKING:
    from modules.household.dtos import EconStateDTO
    from simulation.dtos.config_dtos import HouseholdConfigDTO

class HouseholdFinancialsMixin:
    """
    Mixin for Household financial operations.
    Handles assets, inventory, portfolio, and employment termination.
    """

    # Type hints for properties expected on self
    id: int
    logger: Logger
    config: "HouseholdConfigDTO"
    _econ_state: "EconStateDTO"

    @override
    def _internal_add_assets(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._econ_state.wallet.add(amount, currency, memo="Internal Add")

    @override
    def _internal_sub_assets(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._econ_state.wallet.subtract(amount, currency, memo="Internal Sub")

    @override
    def adjust_assets(self, delta: float, currency: CurrencyCode = DEFAULT_CURRENCY, memo: str = "", tick: int = -1) -> None:
        """
        Adjusts assets by delta (positive or negative).
        """
        if delta > 0:
            self._econ_state.wallet.add(delta, currency, memo, tick)
        elif delta < 0:
            self._econ_state.wallet.subtract(abs(delta), currency, memo, tick)

    def modify_inventory(self, item_id: str, quantity: float) -> None:
        if item_id not in self._econ_state.inventory:
            self._econ_state.inventory[item_id] = 0
        self._econ_state.inventory[item_id] += quantity

    def add_property(self, property_id: int) -> None:
        """Safely adds a property to the owned list."""
        if property_id not in self._econ_state.owned_properties:
            self._econ_state.owned_properties.append(property_id)

    def remove_property(self, property_id: int) -> None:
        """Safely removes a property from the owned list."""
        if property_id in self._econ_state.owned_properties:
            self._econ_state.owned_properties.remove(property_id)

    def quit(self) -> None:
        if self._econ_state.is_employed:
            self.logger.info(f"Household {self.id} is quitting from Firm {self._econ_state.employer_id}")
            self._econ_state.is_employed = False
            self._econ_state.employer_id = None
            self._econ_state.current_wage = 0.0

    def trigger_emergency_liquidation(self) -> List[Any]:
        """
        WO-167: Generates emergency sell orders for all inventory items and stocks.
        Returns list of Order.
        """
        orders = []

        # 1. Liquidate Inventory
        for good, qty in self._econ_state.inventory.items():
            if qty <= 0:
                continue

            price = self._econ_state.perceived_avg_prices.get(good, 10.0)
            liquidation_price = price * self.config.emergency_liquidation_discount

            order = Order(
                agent_id=self.id,
                side="SELL",
                item_id=good,
                quantity=qty,
                price_limit=liquidation_price,
                market_id=good
            )
            orders.append(order)

        # 2. Liquidate Stocks
        for firm_id, holding in self._econ_state.portfolio.holdings.items():
            shares = holding.quantity
            if shares <= 0:
                continue

            # Heuristic price for stock: we don't have access to stock market price here easily
            # without checking markets. We'll use a very low price to ensure sale (market order effectively)
            # or rely on the market to match.
            price = self.config.emergency_stock_liquidation_fallback_price

            order = Order(
                agent_id=self.id,
                side="SELL",
                item_id=f"stock_{firm_id}",
                quantity=shares,
                price_limit=price,
                market_id="stock_market"
            )
            orders.append(order)

        if orders:
            self.logger.warning(
                f"GRACE_PROTOCOL | Household {self.id} triggering emergency liquidation. Generated {len(orders)} orders.",
                extra={"agent_id": self.id, "tags": ["grace_protocol", "liquidation"]}
            )

        return orders

    def add_labor_income(self, income: float) -> None:
        self._econ_state.labor_income_this_tick += income

    def get_desired_wage(self) -> float:
        if self._econ_state.assets.get(DEFAULT_CURRENCY, 0.0) < self.config.household_low_asset_threshold:
            return self.config.household_low_asset_wage
        return self.config.household_default_wage

    def reset_consumption_counters(self) -> None:
        """
        Resets consumption counters for the new tick.
        Used by TickScheduler.
        """
        self._econ_state.current_consumption = 0.0
        self._econ_state.current_food_consumption = 0.0
        self._econ_state.labor_income_this_tick = 0.0
        self._econ_state.capital_income_this_tick = 0.0

    def record_consumption(self, quantity: float, is_food: bool = False) -> None:
        """
        Updates consumption counters.
        Used by Registry during transaction processing.
        """
        self._econ_state.current_consumption += quantity
        if is_food:
            self._econ_state.current_food_consumption += quantity

    # --- IPortfolioHandler Implementation ---

    @property
    def portfolio(self) -> Portfolio:
        """
        Direct access to the internal portfolio object.
        Resolves TD-233 (FinanceDept LoD) and TD-232 (Inheritance).
        """
        return self._econ_state.portfolio

    def get_portfolio(self) -> PortfolioDTO:
        assets = []
        for firm_id, share in self._econ_state.portfolio.holdings.items():
            assets.append(PortfolioAsset(
                asset_type="stock",
                asset_id=str(firm_id),
                quantity=share.quantity
            ))
        return PortfolioDTO(assets=assets)

    def receive_portfolio(self, portfolio: PortfolioDTO) -> None:
        for asset in portfolio.assets:
            if asset.asset_type == "stock":
                try:
                    firm_id = int(asset.asset_id)
                    # TD-160: Inherited assets are integrated.
                    # We use 0.0 acquisition price as default for inheritance if not specified.
                    self._econ_state.portfolio.add(firm_id, asset.quantity, 0.0)
                except ValueError:
                    self.logger.error(f"Invalid firm_id in portfolio receive: {asset.asset_id}")
            else:
                self.logger.warning(f"Household received unhandled asset type: {asset.asset_type} (ID: {asset.asset_id})")

    def clear_portfolio(self) -> None:
        self._econ_state.portfolio.holdings.clear()
