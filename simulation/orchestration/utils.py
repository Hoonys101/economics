from __future__ import annotations
from typing import Dict, Any, TYPE_CHECKING
from simulation.dtos.api import SimulationState
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.markets.order_book_market import OrderBookMarket

if TYPE_CHECKING:
    pass

def prepare_market_data(state: SimulationState) -> Dict[str, Any]:
    """Prepares market data for agent decisions."""
    tracker = state.tracker
    goods_market_data: Dict[str, Any] = {}

    debt_data_map = {}
    deposit_data_map = {}

    # 1. Debt & Deposit Data
    if state.bank:
        for agent_id, agent in state.agents.items():
            if isinstance(agent, (Household, Firm)):
                debt_status = state.bank.get_debt_status(str(agent_id))

                total_burden = 0.0
                ticks_per_year = 100
                if hasattr(state.bank, "_get_config"):
                     ticks_per_year = state.bank._get_config("bank_defaults.ticks_per_year", 100)

                for loan in debt_status.get("loans", []):
                    total_burden += (loan["outstanding_balance"] * loan["interest_rate"]) / ticks_per_year

                debt_data_entry = dict(debt_status)
                debt_data_entry["daily_interest_burden"] = total_burden
                debt_data_entry["total_principal"] = debt_status["total_outstanding_debt"]

                debt_data_map[agent_id] = debt_data_entry
                deposit_data_map[agent_id] = state.bank.get_balance(str(agent_id))

    # 2. Goods Market Data
    for good_name in state.config_module.GOODS:
        market = state.markets.get(good_name)
        if market and isinstance(market, OrderBookMarket):
            avg_price = market.get_daily_avg_price()
            if avg_price <= 0:
                avg_price = market.get_best_ask(good_name) or 0
            if avg_price <= 0:
                latest = tracker.get_latest_indicators()
                avg_price = latest.get(f"{good_name}_avg_price", 0)
            if avg_price <= 0:
                avg_price = state.config_module.GOODS[good_name].get("initial_price", 10.0)

            goods_market_data[f"{good_name}_current_sell_price"] = avg_price

    latest_indicators = tracker.get_latest_indicators()
    avg_wage = latest_indicators.get("labor_avg_price", state.config_module.LABOR_MARKET_MIN_WAGE)

    labor_market = state.markets.get("labor")
    best_wage_offer = 0.0
    job_vacancies = 0

    if labor_market and isinstance(labor_market, OrderBookMarket):
        best_wage_offer = labor_market.get_best_bid("labor") or 0.0
        if best_wage_offer <= 0:
            best_wage_offer = avg_wage

        for item_orders in labor_market.buy_orders.values():
             for order in item_orders:
                 job_vacancies += order.quantity

    goods_market_data["labor"] = {
        "avg_wage": avg_wage,
        "best_wage_offer": best_wage_offer
    }
    goods_market_data["job_vacancies"] = job_vacancies

    total_price = 0.0
    count = 0.0
    for good_name in state.config_module.GOODS:
        price = goods_market_data.get(f"{good_name}_current_sell_price")
        if price is not None:
            total_price += price
            count += 1

    avg_goods_price_for_market_data = total_price / count if count > 0 else 10.0

    stock_market_data = {}
    if state.stock_market:
        for firm in state.firms:
            firm_item_id = f"stock_{firm.id}"
            price = state.stock_market.get_daily_avg_price(firm.id)
            if price <= 0:
                price = state.stock_market.get_best_ask(firm.id) or 0
            if price <= 0:
                price = firm.assets / firm.total_shares if firm.total_shares > 0 else 10.0
            stock_market_data[firm_item_id] = {"avg_price": price}

    rent_prices = [u.rent_price for u in state.real_estate_units if u.owner_id is not None]
    avg_rent = sum(rent_prices) / len(rent_prices) if rent_prices else state.config_module.INITIAL_RENT_PRICE

    housing_market_data = {
        "avg_rent_price": avg_rent
    }

    interest_rate = 0.05
    if state.bank:
        interest_rate = state.bank.base_rate

    return {
        "time": state.time,
        "goods_market": goods_market_data,
        "housing_market": housing_market_data,
        "loan_market": {"interest_rate": interest_rate},
        "stock_market": stock_market_data,
        "all_households": state.households,
        "avg_goods_price": avg_goods_price_for_market_data,
        "debt_data": debt_data_map,
        "deposit_data": deposit_data_map,
        "inflation": latest_indicators.get("inflation_rate", state.config_module.DEFAULT_INFLATION_RATE)
    }
