from typing import List, Optional, Dict, Any
import logging
from simulation.models import Order, StockOrder
from simulation.dtos import DecisionContext, FirmStateDTO, FirmConfigDTO
from modules.finance.api import BorrowerProfileDTO
from simulation.decisions.firm.api import FinancialPlanDTO

logger = logging.getLogger(__name__)

class FinanceManager:
    def formulate_plan(self, context: DecisionContext, dividend_aggressiveness: float, debt_aggressiveness: float) -> FinancialPlanDTO:
        firm = context.state
        config = context.config
        market_data = context.market_data

        orders = []

        # 1. Dividends
        div_order = self._manage_dividends(firm, dividend_aggressiveness, config)
        if div_order:
            orders.append(div_order)

        # 2. Debt
        debt_orders = self._manage_debt(firm, debt_aggressiveness, context)
        orders.extend(debt_orders)

        # 3. Secondary Offering (SEO)
        seo_order = self._attempt_secondary_offering(firm, context, config)
        if seo_order:
            orders.append(seo_order)

        return FinancialPlanDTO(orders=orders)

    def _manage_dividends(self, firm: FirmStateDTO, aggressiveness: float, config: FirmConfigDTO) -> Optional[Order]:
        """
        Set Dividend Rate.
        """
        z_score = firm.altman_z_score
        z_score_threshold = config.altman_z_score_threshold
        loss_limit = config.dividend_suspension_loss_ticks

        is_distressed = (z_score < z_score_threshold) or (firm.consecutive_loss_turns >= loss_limit)

        if is_distressed:
            return Order(firm.id, "SET_DIVIDEND", "internal", 0.0, 0.0, "internal")

        base_rate = config.dividend_rate_min
        max_rate = config.dividend_rate_max
        new_rate = base_rate + (aggressiveness * (max_rate - base_rate))

        return Order(firm.id, "SET_DIVIDEND", "internal", new_rate, 0.0, "internal")

    def _manage_debt(self, firm: FirmStateDTO, aggressiveness: float, context: DecisionContext) -> List[Order]:
        """
        Leverage Management.
        """
        market_data = context.market_data
        orders = []
        target_leverage = aggressiveness * 2.0

        current_debt = 0.0
        debt_info = market_data.get("debt_data", {}).get(firm.id)
        if debt_info:
            current_debt = debt_info.get("total_principal", 0.0)

        current_assets = max(firm.assets, 1.0)
        current_leverage = current_debt / current_assets

        if current_leverage < target_leverage:
            desired_debt = current_assets * target_leverage
            borrow_amount = desired_debt - current_debt
            borrow_amount = min(borrow_amount, current_assets * 0.5)

            if borrow_amount > 100.0:
                # WO-078: Construct BorrowerProfileDTO
                # Retrieve debt info to estimate payments
                daily_burden = 0.0
                if debt_info:
                    daily_burden = debt_info.get("daily_interest_burden", 0.0)

                borrower_profile = BorrowerProfileDTO(
                    borrower_id=str(firm.id),
                    gross_income=firm.revenue_this_turn,
                    existing_debt_payments=daily_burden * 30, # Approx monthly
                    collateral_value=0.0, # Unsecured
                    existing_assets=firm.assets
                )

                # WO-146: Use market rate + spread instead of hardcoded 0.10
                # Fallback: Configured Initial Rate
                base_rate = context.config.initial_base_annual_rate

                # Prioritize Government Policy Rate (Official Base Rate)
                if context.government_policy:
                    base_rate = context.government_policy.base_interest_rate
                # Fallback to Market Data (if available)
                elif "loan_market" in market_data and "interest_rate" in market_data["loan_market"]:
                    base_rate = market_data["loan_market"]["interest_rate"]
                else:
                    logger.warning(f"FINANCE_WARNING | Missing policy/market rate for firm {firm.id}. Used default fallback.")

                # Willingness to pay: base_rate + risk spread
                # Firms usually accept slightly higher than base rate
                spread = context.config.default_loan_spread
                wtp_rate = base_rate + spread

                order = Order(firm.id, "LOAN_REQUEST", "loan", borrow_amount, wtp_rate, "loan")
                order.metadata = {"borrower_profile": borrower_profile}
                orders.append(order)

        elif current_leverage > target_leverage:
            excess_debt = current_debt - (current_assets * target_leverage)
            repay_amount = min(excess_debt, firm.assets * 0.5)

            if repay_amount > 10.0 and current_debt > 0:
                 orders.append(
                    Order(firm.id, "REPAYMENT", "loan", repay_amount, 1.0, "loan")
                )

        return orders

    def _attempt_secondary_offering(self, firm: FirmStateDTO, context: DecisionContext, config: FirmConfigDTO) -> Optional[StockOrder]:
        """Sell treasury shares to raise capital when cash is low."""
        startup_cost = config.startup_cost
        trigger_ratio = config.seo_trigger_ratio

        if firm.assets >= startup_cost * trigger_ratio:
            return None
        if firm.treasury_shares <= 0:
            return None

        # Use DTO
        market_snapshot = context.market_snapshot

        max_sell_ratio = config.seo_max_sell_ratio
        sell_qty = min(firm.treasury_shares * max_sell_ratio, firm.treasury_shares)

        if sell_qty < 1.0:
            return None

        # Determine price (Market Price or Book Value)
        price = 0.0
        if market_snapshot:
             # Try market_signals first (Phase 2 schema)
             if "market_signals" in market_snapshot:
                 signal = market_snapshot["market_signals"].get(f"stock_{firm.id}")
                 if signal:
                     price = signal.get("last_traded_price") or signal.get("best_bid") or 0.0

             # Fallback to legacy market_data if signals failed
             if price <= 0 and "market_data" in market_snapshot:
                 stock_data = market_snapshot["market_data"].get("stock_market", {}).get(f"stock_{firm.id}", {})
                 price = stock_data.get("avg_price", 0.0)

        if price is None or price <= 0:
            # Fallback to Book Value
            if firm.total_shares > 0:
                price = firm.assets / firm.total_shares
            else:
                price = 0.0

        if price <= 0:
            return None

        order = StockOrder(
            agent_id=firm.id,
            firm_id=firm.id,
            order_type="SELL",
            quantity=sell_qty,
            price=price,
            market_id="stock_market"
        )
        logger.info(f"SEO | Firm {firm.id} offering {sell_qty:.1f} shares at {price:.2f}")
        return order
