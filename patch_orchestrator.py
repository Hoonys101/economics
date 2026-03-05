import re

with open('simulation/orchestration/phases/metrics.py', 'r') as f:
    content = f.read()

import_statement = "from modules.analytics.api import EconomyAnalyticsSnapshotDTO, HouseholdAnalyticsDTO, FirmAnalyticsDTO, MarketAnalyticsDTO\n"

if import_statement not in content:
    content = content.replace("from modules.system.api import DEFAULT_CURRENCY", f"from modules.system.api import DEFAULT_CURRENCY\n{import_statement}")


track_block = r'''                m0_dict = self.world_state.calculate_base_money()
                m0_pennies = m0_dict.get(DEFAULT_CURRENCY, 0)

                current_money_dollars = current_money / 100.0
                m2_leak_dollars = m2_leak_delta / 100.0

                state.tracker.track(
                    time=state.time,
                    households=state.households,
                    firms=state.firms,
                    markets=state.markets,
                    money_supply=current_money_dollars,
                    m2_leak=m2_leak_dollars,
                    monetary_base=float(m0_pennies)
                )'''

replacement = r'''                m0_dict = self.world_state.calculate_base_money()
                m0_pennies = m0_dict.get(DEFAULT_CURRENCY, 0)

                # Assemble DTOs
                household_dtos = []
                for h in state.households:
                    h_is_active = h._bio_state.is_active
                    h_cash_pennies = int(state.tracker._calculate_total_wallet_value(h._econ_state.assets)) if h_is_active else 0

                    stock_val = 0.0
                    stock_market = state.markets.get("stock_market")
                    if h_is_active and stock_market and hasattr(stock_market, 'get_stock_price'):
                        for firm_id, holding in h._econ_state.portfolio.holdings.items():
                            if holding.quantity > 0:
                                price = stock_market.get_stock_price(firm_id) or 0.0
                                stock_val += holding.quantity * price

                    household_dtos.append(HouseholdAnalyticsDTO(
                        agent_id=h.id,
                        is_active=h_is_active,
                        total_cash_pennies=h_cash_pennies,
                        portfolio_value_pennies=int(stock_val * 100) if stock_val else 0,
                        is_employed=getattr(h._econ_state, 'is_employed', False),
                        trust_score=getattr(h._social_state, 'trust_score', 0.5) if hasattr(h, '_social_state') else 0.5,
                        survival_need=h._bio_state.needs.get('survival', 0.0) if hasattr(h, '_bio_state') else 0.0,
                        consumption_expenditure_pennies=getattr(h._econ_state, 'consumption_expenditure_this_tick_pennies', 0),
                        food_expenditure_pennies=getattr(h._econ_state, 'food_expenditure_this_tick_pennies', 0),
                        labor_income_pennies=getattr(h._econ_state, 'labor_income_this_tick_pennies', 0),
                        education_level=getattr(h._econ_state, 'education_level', 0.0),
                        aptitude=getattr(h._econ_state, 'aptitude', 0.0)
                    ))

                firm_dtos = []
                for f in state.firms:
                    f_is_active = getattr(f, "is_active", False)
                    f_cash_pennies = 0
                    f_total_assets_pennies = 0
                    if f_is_active:
                        if hasattr(f, "get_all_balances"):
                            f_cash_pennies = int(state.tracker._calculate_total_wallet_value(f.get_all_balances()))
                            usd_cash = f.get_balance(DEFAULT_CURRENCY)
                        elif hasattr(f, "assets"):
                            assets = f.assets
                            if isinstance(assets, dict):
                                f_cash_pennies = int(state.tracker._calculate_total_wallet_value(assets))
                                usd_cash = assets.get(DEFAULT_CURRENCY, 0.0)
                            else:
                                f_cash_pennies = int(assets)
                                usd_cash = assets
                        else:
                            f_cash_pennies = 0
                            usd_cash = 0.0

                        if hasattr(f, "get_financial_snapshot"):
                            snap = f.get_financial_snapshot()
                            snap_total_assets = snap.get("total_assets", 0.0)
                            non_cash_assets = snap_total_assets - usd_cash
                            f_total_assets_pennies = f_cash_pennies + int(non_cash_assets)
                        else:
                            f_total_assets_pennies = f_cash_pennies

                    firm_dtos.append(FirmAnalyticsDTO(
                        agent_id=f.id,
                        is_active=f_is_active,
                        total_assets_pennies=f_total_assets_pennies,
                        cash_balance_pennies=f_cash_pennies,
                        current_production=getattr(f, "current_production", 0.0),
                        inventory_volume=sum(f.get_all_items().values()) if hasattr(f, "get_all_items") and f.get_all_items() else 0.0,
                        sales_volume=getattr(f, "sales_volume_this_tick", 0.0)
                    ))

                market_dtos = []
                for market_id, market in state.markets.items():
                    market_dtos.append(MarketAnalyticsDTO(
                        market_id=market_id,
                        avg_price=market.get_daily_avg_price() if hasattr(market, "get_daily_avg_price") else getattr(market, "avg_price", 0.0),
                        volume=market.get_daily_volume() if hasattr(market, "get_daily_volume") else getattr(market, "volume", 0.0),
                        current_price=getattr(market, "current_price", 0.0)
                    ))

                snapshot = EconomyAnalyticsSnapshotDTO(
                    tick=state.time,
                    households=household_dtos,
                    firms=firm_dtos,
                    markets=market_dtos,
                    money_supply_pennies=current_money,
                    m2_leak_pennies=int(m2_leak_delta),
                    monetary_base_pennies=int(m0_pennies)
                )

                state.tracker.track_tick(snapshot)'''

content = content.replace(track_block, replacement)

with open('simulation/orchestration/phases/metrics.py', 'w') as f:
    f.write(content)
