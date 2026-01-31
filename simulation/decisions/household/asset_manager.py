from typing import List, Dict, Any, Optional
from simulation.models import Order, StockOrder
from simulation.decisions.household.api import AssetManagementContext
from simulation.decisions.portfolio_manager import PortfolioManager
from simulation.decisions.household.stock_trader import StockTrader
from simulation.ai.api import Personality

class AssetManager:
    """
    Manages Financial Assets (Portfolio, Stock, Liquidity, Debt).
    Refactored from AIDrivenHouseholdDecisionEngine.
    """

    def __init__(self):
        self.stock_trader = StockTrader()

    def decide_investments(self, context: AssetManagementContext) -> List[Order]:
        orders = []
        household = context.household
        market_data = context.market_data
        current_time = context.current_time
        config = context.config
        stress_config = context.stress_config
        logger = context.logger

        # 4. Stock Investment Logic
        stock_orders = self._make_stock_investment_decisions(
            context
        )
        orders.extend(stock_orders)

        # 5. Liquidity Management
        # Logic for Debt Repayment (Debt Aversion)
        is_debt_aversion_mode = False
        if stress_config and stress_config.is_active and stress_config.scenario_name == 'deflation':
             if stress_config.debt_aversion_multiplier > 1.0:
                 is_debt_aversion_mode = True

        debt_data = market_data.get("debt_data", {}).get(household.id, {})
        principal = debt_data.get("total_principal", 0.0)

        repay_amount = 0.0
        if is_debt_aversion_mode and principal > 0:
            base_ratio = config.debt_repayment_ratio
            cap_ratio = config.debt_repayment_cap
            liquidity_ratio = config.debt_liquidity_ratio

            repay_amount = household.assets * base_ratio * stress_config.debt_aversion_multiplier
            repay_amount = min(repay_amount, principal * cap_ratio)
            repay_amount = min(repay_amount, household.assets * liquidity_ratio)

            if repay_amount > 1.0:
                 orders.append(Order(
                     agent_id=household.id,
                     side="REPAYMENT",
                     item_id="currency",
                     quantity=repay_amount,
                     price_limit=1.0,
                     market_id="loan_market"
                 ))

                 if logger:
                    logger.info(f"DEBT_AVERSION | Household {household.id} prioritizing repayment: {repay_amount:.1f}")

        # Logic for Portfolio Management vs Emergency Liquidity
        if current_time % 30 == 0:
            # Immutability Fix: Calculate effective cash instead of modifying DTO
            effective_cash = household.assets
            if is_debt_aversion_mode and repay_amount > 0:
                effective_cash -= repay_amount

            portfolio_orders = self._manage_portfolio(context, effective_cash)
            orders.extend(portfolio_orders)
        else:
            emergency_orders = self._check_emergency_liquidity(context)
            orders.extend(emergency_orders)

        return orders

    def get_savings_roi(self, household: Any, market_data: Dict[str, Any], config: Optional[Any] = None) -> float:
        """가계의 저축 ROI(미래 효용)를 계산합니다."""
        if config is None:
            raise ValueError("Config module is required for get_savings_roi")

        loan_market_data = market_data.get("loan_market", {})
        default_rate = getattr(config, "default_mortgage_rate", 0.05)
        nominal_rate = loan_market_data.get("interest_rate", default_rate)

        if household.expected_inflation:
            avg_expected_inflation = sum(household.expected_inflation.values()) / len(household.expected_inflation)
        else:
            avg_expected_inflation = 0.0

        real_rate = nominal_rate - avg_expected_inflation

        beta = 1.0
        if household.personality in [Personality.MISER, Personality.CONSERVATIVE]:
            beta = 1.2
        elif household.personality in [Personality.STATUS_SEEKER, Personality.IMPULSIVE]:
            beta = 0.8

        return (1.0 + real_rate) * beta

    def get_debt_penalty(self, household: Any, market_data: Dict[str, Any], config: Any) -> float:
        debt_data = market_data.get("debt_data", {}).get(household.id, {})
        daily_interest_burden = debt_data.get("daily_interest_burden", 0.0)
        income_proxy = max(household.current_wage, household.assets * 0.01)
        dsr = daily_interest_burden / (income_proxy + 1e-9)

        debt_penalty = 1.0
        if dsr > config.dsr_critical_threshold:
            debt_penalty = 0.5 # 50% reduction in aggressiveness due to liquidity panic
        return debt_penalty

    def _manage_portfolio(self, context: AssetManagementContext, available_cash: float) -> List[Order]:
        orders = []
        household = context.household
        config = context.config
        market_data = context.market_data
        macro_context = context.macro_context

        # Use available_cash (effective assets)
        cash = available_cash
        deposit_data = market_data.get("deposit_data", {})
        deposit_balance = deposit_data.get(household.id, 0.0)
        total_liquid = cash + deposit_balance

        risk_aversion = household.risk_aversion

        loan_market = market_data.get("loan_market", {})
        risk_free_rate = loan_market.get("interest_rate", config.default_mortgage_rate)

        equity_return = getattr(config, "expected_startup_roi", 0.15)

        goods_market = market_data.get("goods_market", {})
        food_price = goods_market.get("basic_food_current_sell_price", 5.0)
        daily_consumption = getattr(config, "household_food_consumption_per_tick", 2.0)
        monthly_survival_cost = food_price * daily_consumption * 30.0

        if household.expected_inflation:
            avg_inflation = sum(household.expected_inflation.values()) / len(household.expected_inflation)
        else:
            avg_inflation = 0.0

        target_cash, target_deposit, target_equity = PortfolioManager.optimize_portfolio(
            total_liquid_assets=total_liquid,
            risk_aversion=risk_aversion,
            risk_free_rate=risk_free_rate,
            equity_return_proxy=equity_return,
            survival_cost=monthly_survival_cost,
            inflation_expectation=avg_inflation,
            macro_context=macro_context
        )

        diff_deposit = target_deposit - deposit_balance

        if diff_deposit > 10.0:
            actual_deposit = min(cash, diff_deposit)
            if actual_deposit > 10.0:
                orders.append(Order(
                    agent_id=household.id,
                    side="DEPOSIT",
                    item_id="currency",
                    quantity=actual_deposit,
                    price_limit=1.0,
                    market_id="currency"
                ))

        elif diff_deposit < -10.0:
            amount_to_withdraw = abs(diff_deposit)
            orders.append(Order(
                agent_id=household.id,
                side="WITHDRAW",
                item_id="currency",
                quantity=amount_to_withdraw,
                price_limit=1.0,
                market_id="currency"
            ))


        startup_cost = getattr(config, "startup_cost", 30000.0)

        if target_equity >= startup_cost * 0.8:
            projected_cash = cash - max(0, diff_deposit) + max(0, -diff_deposit)
            survival_buffer = 2000.0

            if projected_cash >= (startup_cost + survival_buffer):
                orders.append(Order(
                    agent_id=household.id,
                    side="INVEST",
                    item_id="startup",
                    quantity=1.0,
                    price_limit=startup_cost,
                    market_id="admin"
                ))


        return orders

    def _check_emergency_liquidity(self, context: AssetManagementContext) -> List[Order]:
        orders = []
        household = context.household
        market_data = context.market_data

        if household.assets < 10.0:
            deposit_data = market_data.get("deposit_data", {})
            deposit_balance = deposit_data.get(household.id, 0.0)

            if deposit_balance > 10.0:
                amount = min(deposit_balance, 50.0)
                orders.append(Order(
                    agent_id=household.id,
                    side="WITHDRAW",
                    item_id="currency",
                    quantity=amount,
                    price_limit=1.0,
                    market_id="currency"
                ))


        return orders

    def _make_stock_investment_decisions(self, context: AssetManagementContext) -> List[StockOrder]:
        stock_orders: List[StockOrder] = []
        household = context.household
        config = context.config
        market_snapshot = context.market_snapshot
        market_data = context.market_data
        macro_context = context.macro_context

        if not getattr(config, "stock_market_enabled", False):
            return stock_orders

        if market_snapshot is None:
            return stock_orders

        if household.assets < config.household_min_assets_for_investment:
            return stock_orders

        avg_dividend_yield = market_data.get("avg_dividend_yield", 0.05)
        risk_free_rate = market_data.get("loan_market", {}).get("interest_rate", 0.03)

        goods_market = market_data.get("goods_market", {})
        food_price = goods_market.get("basic_food_current_sell_price", 5.0)
        if not food_price or food_price <= 0:
             food_price = config.goods.get("basic_food", {}).get("initial_price", 5.0)

        daily_consumption = getattr(config, "household_food_consumption_per_tick", 2.0)
        survival_cost = food_price * daily_consumption * 30.0

        risk_aversion = self._get_risk_aversion(household.personality)

        target_cash, target_deposit, target_equity = PortfolioManager.optimize_portfolio(
            total_liquid_assets=household.assets,
            risk_aversion=risk_aversion,
            risk_free_rate=risk_free_rate,
            equity_return_proxy=avg_dividend_yield,
            survival_cost=survival_cost,
            inflation_expectation=market_data.get("inflation", 0.02),
            macro_context=macro_context
        )

        current_prices = {}
        if market_snapshot:
            # Handle TypedDict/Legacy compatibility
            prices = getattr(market_snapshot, "prices", None)
            if prices is None and isinstance(market_snapshot, dict):
                # Try new schema first
                signals = market_snapshot.get("market_signals", {})

                # Check legacy data
                if not signals:
                    legacy_data = market_snapshot.get("market_data", {})
                    # Legacy market data structure for stocks was stock_market_data[firm_item_id]
                    # We need to adapt.
                    # Or we just iterate signals.
                    pass

                for firm_id in household.portfolio_holdings.keys():
                    item_id = f"stock_{firm_id}"
                    price = 0.0

                    if item_id in signals:
                        signal = signals[item_id]
                        price = signal.get('last_traded_price') or signal.get('best_ask') or 0.0
                    else:
                        # Fallback to legacy price extraction logic if needed or assume 0
                        # Usually price extraction from legacy market_data is complex.
                        # Assuming signals are available if market_snapshot is passed.
                        pass

                    current_prices[firm_id] = price

            elif prices:
                for firm_id in household.portfolio_holdings.keys():
                    price = prices.get(f"stock_{firm_id}", 0.0)
                    current_prices[firm_id] = price

        # Calculate valuation manually for DTO
        current_equity_value = 0.0
        for fid, share in household.portfolio_holdings.items():
            price = current_prices.get(fid, 0.0)
            current_equity_value += share.quantity * price

        equity_delta = target_equity - current_equity_value

        if equity_delta > config.stock_investment_equity_delta_threshold:
            stock_orders.extend(self.stock_trader.place_buy_orders(household, equity_delta, market_snapshot, config, context.logger))
        elif equity_delta < -config.stock_investment_equity_delta_threshold:
            stock_orders.extend(self.stock_trader.place_sell_orders(household, -equity_delta, market_snapshot, config, context.logger))

        return stock_orders

    def _get_risk_aversion(self, personality_type: Personality) -> float:
        if personality_type == Personality.STATUS_SEEKER:
            return 0.5
        elif personality_type == Personality.CONSERVATIVE:
            return 5.0
        return 2.0
