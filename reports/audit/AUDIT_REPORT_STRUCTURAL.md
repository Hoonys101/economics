# AUDIT_REPORT_STRUCTURAL: Structural Integrity Audit (v3.0)

## 1. God Class Candidates (Lines > 800 or Public Methods > 15)
- `simulation/firms.py` : **Firm** (Lines: 1875, Public Methods: 100)
- `simulation/core_agents.py` : **Household** (Lines: 1256, Public Methods: 102)
- `simulation/systems/settlement_system.py` : **FinancialSentry** (Lines: 1024, Public Methods: 1)
- `simulation/systems/settlement_system.py` : **InventorySentry** (Lines: 1024, Public Methods: 1)
- `simulation/systems/settlement_system.py` : **SettlementSystem** (Lines: 1024, Public Methods: 25)
- `simulation/agents/government.py` : **Government** (Lines: 802, Public Methods: 37)
- `simulation/markets/order_book_market.py` : **OrderBookMarket** (Lines: 470, Public Methods: 23)
- `simulation/bank.py` : **Bank** (Lines: 429, Public Methods: 28)
- `simulation/agents/central_bank.py` : **CentralBank** (Lines: 428, Public Methods: 20)
- `simulation/world_state.py` : **WorldState** (Lines: 395, Public Methods: 36)
- `simulation/markets/stock_market.py` : **StockMarket** (Lines: 305, Public Methods: 16)
- `simulation/systems/lifecycle/adapters.py` : **BirthContextAdapter** (Lines: 280, Public Methods: 23)
- `simulation/systems/lifecycle/adapters.py` : **DeathContextAdapter** (Lines: 280, Public Methods: 23)
- `simulation/components/demographics_component.py` : **DemographicsComponent** (Lines: 152, Public Methods: 19)

## 2. Protocol Evasion Candidates (`hasattr` / `isinstance`)
### `simulation/systems/settlement_system.py`
- Line 146: `if self.estate_registry and hasattr(self._transaction_engine.validator.account_accessor, 'set_estate_registry'):`
- Line 157: `if isinstance(agent, IAgent) or isinstance(agent, IFinancialAgent):`
- Line 216: `if currency == DEFAULT_CURRENCY and isinstance(agent, IFinancialEntity):`
- Line 219: `if isinstance(agent, IFinancialAgent):`
- Line 226: `if currency == DEFAULT_CURRENCY and isinstance(dead_agent, IFinancialEntity):`
- ... and 28 more.
### `simulation/systems/housing_system.py`
- Line 61: `if bank and hasattr(bank, 'loans'): # Legacy attribute check, ideally should use IBankService.get_loan_by_id`
- Line 66: `if loan and hasattr(loan, 'remaining_balance') and loan.remaining_balance > 0:`
- Line 78: `if is_dataclass(lien) or isinstance(lien, LienDTO):`
- Line 80: `elif isinstance(lien, dict):`
- Line 92: `if isinstance(old_owner_agent, IPropertyOwner) and unit.id in old_owner_agent.owned_properties:`
- ... and 19 more.
### `simulation/systems/registry.py`
- Line 72: `if isinstance(seller, Household):`
- Line 76: `if isinstance(previous_employer, Firm):`
- Line 77: `if hasattr(previous_employer, 'hr_engine') and hasattr(previous_employer, 'hr_state'):`
- Line 79: `elif hasattr(previous_employer, 'hr'): # Legacy fallback if needed`
- Line 87: `if isinstance(buyer, Firm):`
- ... and 16 more.
### `simulation/systems/lifecycle/death_system.py`
- Line 43: `if not isinstance(context, IDeathContext):`
- Line 63: `if isinstance(firm, ILiquidatable):`
- Line 69: `if hasattr(firm, 'hr_state'):`
- Line 74: `if hasattr(employee, 'is_employed'):`
- Line 80: `if isinstance(firm, ICurrencyHolder):`
- ... and 14 more.
### `simulation/systems/handlers/goods_handler.py`
- Line 27: `if isinstance(tx.total_pennies, float):`
- Line 30: `if not isinstance(tx.total_pennies, int):`
- Line 61: `if isinstance(buyer, ISolvencyChecker):`
- Line 64: `if isinstance(buyer, IFinancialAgent):`
- Line 69: `if isinstance(current_assets, dict):`
- ... and 13 more.
### `simulation/firms.py`
- Line 157: `if not isinstance(self.hr_engine, IHREngine): raise TypeError("hr_engine violation")`
- Line 158: `if not isinstance(self.finance_engine, IFinanceEngine): raise TypeError("finance_engine violation")`
- Line 159: `if not isinstance(self.production_engine, IProductionEngine): raise TypeError("production_engine violation")`
- Line 160: `if not isinstance(self.sales_engine, ISalesEngine): raise TypeError("sales_engine violation")`
- Line 161: `if not isinstance(self.asset_management_engine, IAssetManagementEngine): raise TypeError("asset_management_engine violation")`
- ... and 12 more.
### `simulation/ai/household_ai.py`
- Line 80: `if self.ai_decision_engine and hasattr(self.ai_decision_engine, "context") and self.ai_decision_engine.context:`
- Line 130: `if isinstance(assets_data, dict):`
- Line 186: `if not isinstance(survival_threshold, (int, float)):`
- Line 212: `if not isinstance(goods_dict, dict):`
- Line 216: `if not isinstance(good_info, dict):`
- ... and 10 more.
### `simulation/agents/government.py`
- Line 76: `if isinstance(initial_assets, dict):`
- Line 226: `inf_sma = dto.inflation_sma if isinstance(dto.inflation_sma, (int, float)) else 0.0`
- Line 227: `app_sma = dto.approval_sma if isinstance(dto.approval_sma, (int, float)) else 0.0`
- Line 295: `if decision_legacy and isinstance(decision_legacy, dict):`
- Line 447: `if hasattr(self.finance_system, 'bank'): buyer_pool['bank'] = self.finance_system.bank`
- ... and 9 more.
### `simulation/decisions/household/consumption_manager.py`
- Line 21: `if not isinstance(emergency_threshold, (int, float)):`
- Line 27: `if not isinstance(food_id, str):`
- Line 31: `if isinstance(market_snapshot, dict):`
- Line 35: `if isinstance(signals, dict):`
- Line 38: `if hasattr(signal, 'best_ask') and signal.best_ask is not None:`
- ... and 8 more.
### `simulation/systems/event_system.py`
- Line 61: `if hasattr(h, 'wallet'):`
- Line 63: `elif hasattr(h._econ_state, 'assets') and isinstance(h._econ_state.assets, dict):`
- Line 67: `assets_val = float(h._econ_state.assets) if hasattr(h._econ_state, 'assets') else 0.0`
- Line 91: `if hasattr(agent, 'wallet'):`
- Line 93: `elif hasattr(agent, 'assets') and isinstance(agent.assets, dict):`
- ... and 8 more.
### `simulation/loan_market.py`
- Line 72: `if isinstance(regulations, dict):`
- Line 82: `if isinstance(housing_config, dict):`
- Line 103: `if hasattr(self.bank, 'get_interest_rate'):`
- Line 147: `if hasattr(self.bank, 'get_interest_rate'):`
- Line 180: `if hasattr(self.bank, 'loans') and staged_loan_id in self.bank.loans:`
- ... and 7 more.
### `simulation/decisions/ai_driven_firm_engine.py`
- Line 59: `if not hasattr(order, 'item_id'):`
- Line 66: `if isinstance(signals, dict):`
- Line 72: `if not isinstance(max_staleness, (int, float)):`
- Line 79: `if not isinstance(margin, (int, float)):`
- Line 88: `if not isinstance(fire_sale_asset_threshold, (int, float)):`
- ... and 7 more.
### `simulation/orchestration/phases/decision.py`
- Line 55: `if hasattr(firm.decision_engine, 'ai_engine') and firm.decision_engine.ai_engine:`
- Line 60: `market_insight = firm.market_insight if hasattr(firm, 'market_insight') else 0.5`
- Line 71: `if hasattr(decision_output, 'orders'):`
- Line 89: `if hasattr(household.decision_engine, 'ai_engine') and household.decision_engine.ai_engine:`
- Line 93: `market_insight = household._econ_state.market_insight if hasattr(household, '_econ_state') else 0.5`
- ... and 7 more.
### `simulation/orchestration/phases/metrics.py`
- Line 112: `if h_is_active and stock_market and hasattr(stock_market, 'get_stock_price'):`
- Line 124: `trust_score=getattr(h._social_state, 'trust_score', 0.5) if hasattr(h, '_social_state') else 0.5,`
- Line 125: `survival_need=h._bio_state.needs.get('survival', 0.0) if hasattr(h, '_bio_state') else 0.0,`
- Line 139: `if hasattr(f, "get_all_balances"):`
- Line 142: `elif hasattr(f, "assets"):`
- ... and 7 more.
### `simulation/systems/handlers/stock_handler.py`
- Line 42: `if hasattr(seller, "portfolio"):`
- Line 44: `elif isinstance(seller, Household) and hasattr(seller, "shares_owned"):`
- Line 50: `elif isinstance(seller, Firm) and seller.id == firm_id:`
- Line 55: `if hasattr(buyer, "portfolio"):`
- Line 59: `elif isinstance(buyer, Household) and hasattr(buyer, "shares_owned"):`
- ... and 7 more.
### `simulation/orchestration/phases/post_sequence.py`
- Line 32: `housing_market=state.markets.get('housing') if hasattr(state, 'markets') else None`
- Line 39: `if hasattr(self.world_state, 'lifecycle_manager') and self.world_state.lifecycle_manager:`
- Line 64: `if hasattr(firm.decision_engine, 'ai_engine'):`
- Line 77: `run_id=state.agents.get(firm.id).run_id if hasattr(state.agents.get(firm.id), 'run_id') else 0,`
- Line 90: `if hasattr(household.decision_engine, 'ai_engine') and household.decision_engine.ai_engine:`
- ... and 5 more.
### `simulation/systems/handlers/monetary_handler.py`
- Line 27: `if isinstance(tx.total_pennies, float):`
- Line 30: `if not isinstance(tx.total_pennies, int):`
- Line 111: `if isinstance(seller, IInvestor):`
- Line 113: `elif isinstance(seller, IIssuer) and seller.id == firm_id:`
- Line 117: `if isinstance(buyer, IInvestor):`
- ... and 5 more.
### `simulation/systems/handlers/public_manager_handler.py`
- Line 81: `if isinstance(buyer, Firm):`
- Line 83: `# AccountingSystem: "if isinstance(buyer, Firm): ... buyer.finance.record_expense(amount)"`
- Line 103: `if isinstance(buyer, Household):`
- Line 107: `if isinstance(buyer, IInventoryHandler):`
- Line 108: `slot = InventorySlot.INPUT if is_raw_material and isinstance(buyer, Firm) else InventorySlot.MAIN`
- ... and 4 more.
### `simulation/initialization/initializer.py`
- Line 267: `if hasattr(sim, 'government'):`
- Line 276: `if hasattr(sim, 'central_bank') and sim.central_bank:`
- Line 290: `if hasattr(sim.public_manager, 'id') and sim.public_manager.id == ID_PUBLIC_MANAGER:`
- Line 395: `if hasattr(firm, 'init_ipo'):`
- Line 566: `if demographic_manager_local and hasattr(hh, 'demographic_manager'):`
- ... and 3 more.
### `simulation/systems/handlers/asset_transfer_handler.py`
- Line 47: `if isinstance(seller, IPropertyOwner) and unit_id in seller.owned_properties:`
- Line 49: `if isinstance(buyer, IPropertyOwner):`
- Line 66: `if isinstance(seller, IInvestor):`
- Line 68: `elif isinstance(seller, Firm) and seller.id == firm_id:`
- Line 72: `if isinstance(buyer, IInvestor):`
- ... and 3 more.
### `simulation/systems/lifecycle/aging_system.py`
- Line 28: `if not isinstance(context, IAgingContext):`
- Line 57: `if not isinstance(firm, IAgingFirm) or not firm.is_active:`
- Line 67: `if isinstance(firm.finance_engine, IFinanceEngine):`
- Line 73: `if isinstance(firm, ICurrencyHolder):`
- Line 75: `elif isinstance(firm.wallet, IFinancialEntity): # Fallback via wallet`
- ... and 3 more.
### `simulation/engine.py`
- Line 125: `if isinstance(prop, property) and prop.fset:`
- Line 135: `if hasattr(self, "world_state") and (hasattr(self.world_state, name) or name not in self.__dict__):`
- Line 152: `if hasattr(self, "lock_manager") and self.lock_manager:`
- Line 158: `elif hasattr(self, "_lock_file") and self._lock_file:`
- Line 233: `if key.endswith("_current_sell_price") and isinstance(value, (int, float)) and value > 0:`
- ... and 2 more.
### `simulation/bank.py`
- Line 56: `if isinstance(initial_assets, dict):`
- Line 154: `if isinstance(amount, float):`
- Line 156: `if not isinstance(amount, int):`
- Line 164: `if hasattr(borrower_id, 'id'):`
- Line 172: `if not hasattr(self.finance_system, 'process_loan_application'):`
- ... and 2 more.
### `simulation/orchestration/dashboard_service.py`
- Line 25: `if hasattr(simulation_or_state, 'world_state'):`
- Line 45: `if isinstance(tracker, IEconomicIndicatorTracker):`
- Line 64: `if isinstance(tracker, IEconomicIndicatorTracker):`
- Line 115: `party = gov.ruling_party.name if hasattr(gov.ruling_party, 'name') else str(gov.ruling_party)`
- Line 148: `if repo and hasattr(repo, "agents"):`
- ... and 2 more.
### `simulation/systems/bootstrapper.py`
- Line 37: `if hasattr(central_bank, 'id'):`
- Line 40: `if is_cb and hasattr(settlement_system, 'create_and_transfer'):`
- Line 43: `if isinstance(target_agent, IBank):`
- Line 92: `if not isinstance(settlement_system, IMonetaryAuthority):`
- Line 94: `if not isinstance(central_bank, ICentralBank):`
- ... and 2 more.
### `simulation/systems/accounting.py`
- Line 26: `if hasattr(seller, 'record_revenue'):`
- Line 34: `if hasattr(seller, 'finance_state') and hasattr(seller.finance_state, 'sales_volume_this_tick'):`
- Line 37: `elif hasattr(seller, 'sales_volume_this_tick'):`
- Line 40: `elif hasattr(seller, 'labor_income_this_tick'):`
- Line 53: `if hasattr(buyer, 'record_expense'):`
- ... and 2 more.
### `simulation/systems/handlers/financial_handler.py`
- Line 28: `if success and isinstance(buyer, IExpenseTracker):`
- Line 34: `if success and isinstance(buyer, Household):`
- Line 39: `if hasattr(buyer, "capital_income_this_tick"):`
- Line 67: `if isinstance(buyer, IExpenseTracker):`
- Line 77: `if isinstance(seller, ILoanRepayer):`
- ... and 2 more.
### `simulation/registries/estate_registry.py`
- Line 26: `if agent and hasattr(agent, 'id'):`
- Line 37: `if isinstance(agent_id, str) and agent_id.isdigit():`
- Line 69: `if isinstance(agent, IFinancialEntity):`
- Line 71: `elif isinstance(agent, IFinancialAgent):`
- Line 75: `if hasattr(agent, 'balance_pennies'):`
- ... and 1 more.
### `simulation/decisions/household/labor_manager.py`
- Line 26: `if hasattr(action_vector, 'job_mobility_aggressiveness'):`
- Line 32: `if current_wage is None and hasattr(household, 'current_wage_pennies'):`
- Line 45: `if isinstance(household_assets, dict):`
- Line 69: `if hasattr(household, 'agent_data'):`
- Line 71: `elif hasattr(household, 'get_agent_data'):`
- ... and 1 more.
### `simulation/orchestration/factories.py`
- Line 29: `if isinstance(market, OrderBookMarket):`
- Line 104: `if hasattr(state, 'real_estate_units') and state.real_estate_units:`
- Line 108: `if housing_market and hasattr(housing_market, "sell_orders"):`
- Line 162: `if state.tracker and hasattr(state.tracker, "capture_market_context"):`
- Line 174: `if gov and hasattr(gov, "state"):`
- ... and 1 more.
### `simulation/orchestration/agent_service.py`
- Line 35: `if isinstance(agent, IAgent):`
- Line 45: `if isinstance(agent, (Household, Firm)):`
- Line 70: `if isinstance(agent, Household):`
- Line 78: `elif isinstance(agent, Firm):`
- Line 102: `if isinstance(agent, Household):`
- ... and 1 more.
### `simulation/orchestration/utils.py`
- Line 24: `if isinstance(agent, (Household, Firm)):`
- Line 29: `if hasattr(state.bank, "_get_config"):`
- Line 35: `elif isinstance(debt_status, dict):`
- Line 65: `if market and isinstance(market, OrderBookMarket):`
- Line 84: `if labor_market and isinstance(labor_market, OrderBookMarket):`
- ... and 1 more.
### `simulation/ai/firm_ai.py`
- Line 71: `if isinstance(assets_raw, dict):`
- Line 76: `elif isinstance(assets_raw, MultiCurrencyWalletDTO):`
- Line 202: `if isinstance(current_assets_raw, dict):`
- Line 207: `elif isinstance(current_assets_raw, MultiCurrencyWalletDTO):`
- Line 212: `if isinstance(prev_assets_raw, dict):`
- ... and 1 more.
### `simulation/ai/vectorized_planner.py`
- Line 58: `children_counts.append(float(len(v)) if isinstance(v, list) else 0.0)`
- Line 69: `if hasattr(self, "config") and self.config is not None:`
- Line 114: `if hasattr(a.assets, 'get'):`
- Line 125: `if hasattr(a.needs, 'get'):`
- Line 135: `if hasattr(market_data, 'get'):`
- ... and 1 more.
### `simulation/ai/ai_training_manager.py`
- Line 101: `if hasattr(child_agent.decision_engine, "ai_engine"):`
- Line 137: `if not hasattr(source_agent, "decision_engine") or not hasattr(`
- Line 143: `if not hasattr(source_agent.decision_engine, "ai_engine") or not hasattr(target_agent.decision_engine, "ai_engine"):`
- Line 150: `if hasattr(source_ai, "q_consumption") and hasattr(target_ai, "q_consumption"):`
- Line 160: `if hasattr(source_ai, "q_work") and hasattr(target_ai, "q_work"):`
- ... and 1 more.
### `simulation/systems/inheritance_manager.py`
- Line 52: `if hasattr(deceased, '_econ_state') and hasattr(deceased._econ_state, 'wallet'):`
- Line 63: `if isinstance(cash_raw, dict):`
- Line 164: `if hasattr(tx, 'metadata') and hasattr(tx.metadata, 'original_metadata'):`
- Line 197: `if hasattr(tx, 'metadata') and hasattr(tx.metadata, 'original_metadata'):`
- Line 272: `if hasattr(tx, 'metadata') and hasattr(tx.metadata, 'original_metadata'):`
- ... and 1 more.
### `simulation/systems/analytics_system.py`
- Line 44: `if isinstance(agent, Household):`
- Line 93: `elif isinstance(agent, Firm):`
- Line 127: `if hasattr(agent, 'get_assets_by_currency'):`
- Line 183: `if hasattr(h, 'create_snapshot_dto'):`
- Line 192: `hh_assets_val = int(hh_assets.get(DEFAULT_CURRENCY, 0.0) if isinstance(hh_assets, dict) else hh_assets)`
- ... and 1 more.
### `simulation/systems/firm_management.py`
- Line 40: `avg_p_pennies = round_to_pennies(avg_p * 100) if isinstance(avg_p, float) else avg_p`
- Line 62: `if isinstance(assets, dict):`
- Line 75: `max_id = max([a.id for a in simulation.agents.values() if isinstance(a.id, int)], default=0)`
- Line 175: `active_firms_count = sum(1 for a in simulation.agents.values() if isinstance(a, Firm) and a.is_active)`
- Line 178: `households = [a for a in simulation.agents.values() if isinstance(a, Household) and a.is_active]`
- ... and 1 more.
### `simulation/systems/demographic_manager.py`
- Line 39: `if hasattr(self, "initialized") and self.initialized:`
- Line 105: `if hasattr(agent, '_econ_state'):`
- Line 107: `if hasattr(agent, 'portfolio') and agent.portfolio is not None:`
- Line 109: `if hasattr(agent, 'bio_state'):`
- Line 153: `if hasattr(parent, 'wallet'):`
- ... and 1 more.
### `simulation/systems/handlers/labor_handler.py`
- Line 87: `if hasattr(context, "transaction_queue"):`
- Line 114: `if isinstance(seller, Household):`
- Line 124: `if isinstance(previous_employer, Firm):`
- Line 137: `if isinstance(seller, IIncomeTracker):`
- Line 141: `if isinstance(buyer, Firm):`
- ... and 1 more.
### `simulation/decisions/action_proposal.py`
- Line 31: `if hasattr(agent, 'wallet'):`
- Line 33: `elif hasattr(agent, 'assets') and isinstance(agent.assets, dict):`
- Line 35: `elif hasattr(agent, 'assets'):`
- Line 52: `if hasattr(agent, 'decision_engine') and hasattr(agent.decision_engine, 'context'):`
- Line 66: `if hasattr(self.config_module, 'get'):`
### `simulation/decisions/firm/financial_strategy.py`
- Line 56: `if isinstance(current_assets_raw, dict):`
- Line 70: `if isinstance(gross_income_raw, dict):`
- Line 97: `if isinstance(current_balance_raw, dict):`
- Line 111: `if isinstance(signals, dict):`
- Line 117: `if isinstance(m_data, dict):`
### `simulation/models.py`
- Line 32: `if isinstance(self.metadata, dict):`
- Line 39: `if isinstance(self.total_pennies, float):`
- Line 118: `if hasattr(lien, 'lien_type') and lien.lien_type == 'MORTGAGE':`
- Line 120: `elif isinstance(lien, dict) and lien.get('lien_type') == 'MORTGAGE':`
### `simulation/factories/firm_factory.py`
- Line 70: `if hasattr(birth_context, "agent_registry") and birth_context.agent_registry:`
- Line 74: `if hasattr(birth_context, "firms"):`
- Line 146: `if hasattr(birth_context, "agent_registry") and birth_context.agent_registry:`
- Line 148: `elif hasattr(birth_context, "firms"):`
### `simulation/decisions/household/stock_trader.py`
- Line 20: `if isinstance(signals, dict):`
- Line 28: `if isinstance(m_data, dict):`
- Line 45: `if isinstance(m_data, dict) and "stock_market" in m_data:`
- Line 49: `if isinstance(signals, dict):`
### `simulation/decisions/firm/production_strategy.py`
- Line 85: `if isinstance(current_assets_raw, dict):`
- Line 107: `if isinstance(current_revenue_raw, dict):`
- Line 111: `if isinstance(current_assets_raw, dict):`
- Line 133: `if isinstance(current_assets_raw, dict):`
### `simulation/orchestration/phases/pre_sequence.py`
- Line 26: `if state.bank and hasattr(state.bank, "generate_solvency_transactions"):`
- Line 83: `if state.central_bank and hasattr(state.central_bank, "step"):`
- Line 94: `if state.central_bank and hasattr(state.central_bank, "potential_gdp"):`
- Line 109: `if state.bank and hasattr(state.bank, "update_base_rate"):`
### `simulation/ai/system2_planner.py`
- Line 42: `if hasattr(self.agent, 'wallet'):`
- Line 44: `elif hasattr(self.agent, 'assets') and isinstance(self.agent.assets, dict):`
- Line 46: `elif hasattr(self.agent, 'assets'):`
- Line 62: `if household_ai and hasattr(household_ai, "decide_time_allocation"):`
### `simulation/systems/ma_manager.py`
- Line 31: `elif isinstance(simulation.settlement_system, IMonetaryAuthority):`
- Line 54: `avg_p_pennies = round_to_pennies(avg_p * 100) if isinstance(avg_p, float) else avg_p`
- Line 116: `if hasattr(predator, "system2_planner") and predator.system2_planner:`
- Line 210: `if hasattr(prey, "automation_level") and hasattr(predator, "automation_level"):`
### `simulation/systems/transaction_processor.py`
- Line 56: `if not hasattr(self, "taxation_system"):`
- Line 160: `if hasattr(tx, "metadata") and tx.metadata:`
- Line 161: `if hasattr(tx.metadata, "original_metadata") and tx.metadata.original_metadata:`
- Line 163: `elif hasattr(tx.metadata, "get"):`
### `simulation/world_state.py`
- Line 337: `and hasattr(agent, "value_orientation")`
- Line 368: `if attr_name.startswith('_') or isinstance(attr_value, (int, float, str, bool, type(None))):`
- Line 372: `if hasattr(attr_value, 'teardown') and callable(attr_value.teardown):`
### `simulation/core_agents.py`
- Line 699: `if hasattr(decision_output, "orders"):`
- Line 972: `if hasattr(self.decision_engine, 'ai_engine'):`
- Line 1239: `elif hasattr(government_state, 'income_tax_rate') and government_state.income_tax_rate > 0.2:`
### `simulation/policies/adaptive_gov_policy.py`
- Line 75: `if hasattr(self.config, 'adaptive_policy'):`
- Line 77: `if isinstance(ap, dict):`
- Line 84: `elif isinstance(self.config, dict) and 'adaptive_policy' in self.config:`
### `simulation/factories/agent_factory.py`
- Line 57: `if decision_engine and hasattr(decision_engine, 'value_orientation'):`
- Line 165: `if hasattr(simulation, "ai_training_manager") and simulation.ai_training_manager:`
- Line 193: `if strategy and hasattr(strategy, "newborn_engine_type") and strategy.newborn_engine_type:`
### `simulation/decisions/rule_based_household_engine.py`
- Line 55: `current_assets = state.assets.get("USD", 0) if isinstance(state.assets, dict) else state.assets`
- Line 62: `assets_val = state.assets.get("USD", 0) if isinstance(state.assets, dict) else state.assets`
- Line 104: `if hasattr(state, 'shadow_reservation_wage_pennies') and state.shadow_reservation_wage_pennies > 0:`
### `simulation/decisions/household/asset_manager.py`
- Line 21: `if isinstance(assets, dict):`
- Line 174: `if not isinstance(signals, dict):`
- Line 178: `if not isinstance(legacy_data, dict):`
### `simulation/decisions/firm/hr_strategy.py`
- Line 88: `cash = balance.get(DEFAULT_CURRENCY, 0.0) if isinstance(balance, dict) else float(balance)`
- Line 97: `cash = balance.get(DEFAULT_CURRENCY, 0.0) if isinstance(balance, dict) else float(balance)`
- Line 103: `cash = balance.get(DEFAULT_CURRENCY, 0.0) if isinstance(balance, dict) else float(balance)`
### `simulation/orchestration/phases/intercept.py`
- Line 32: `if not hasattr(world_state, 'global_registry') or not world_state.global_registry:`
- Line 39: `if hasattr(world_state.settlement_system, 'agent_registry'):`
- Line 44: `if hasattr(world_state, 'agent_registry'):`
### `simulation/orchestration/phases/matching.py`
- Line 22: `if isinstance(market, OrderBookMarket):`
- Line 24: `elif isinstance(market, ILaborMarket):`
- Line 26: `if hasattr(market, 'match_orders'):`
### `simulation/db/logger.py`
- Line 48: `if isinstance(snapshot_data, dict):`
- Line 60: `if isinstance(m2, dict):`
- Line 103: `if hasattr(self, 'conn') and self.conn:`
### `simulation/ai/firm_system2_planner.py`
- Line 52: `if isinstance(revenue_raw, dict):`
- Line 66: `if isinstance(personality_data, Personality):`
- Line 81: `if isinstance(assets_raw, dict):`
### `simulation/systems/generational_wealth_audit.py`
- Line 36: `if hasattr(agent, 'wallet'):`
- Line 38: `elif hasattr(agent, 'assets') and isinstance(agent.assets, dict):`
- Line 40: `elif hasattr(agent, 'assets'):`
### `simulation/systems/commerce_system.py`
- Line 92: `cash = assets.get(DEFAULT_CURRENCY, 0.0) if isinstance(assets, dict) else float(assets)`
- Line 151: `cash = assets.get(DEFAULT_CURRENCY, 0.0) if isinstance(assets, dict) else float(assets)`
- Line 210: `is_real_amount = not isinstance(edu_amt, MagicMock) and float(edu_amt) > 0`
### `simulation/systems/central_bank_system.py`
- Line 35: `self._id = central_bank_agent.id if hasattr(central_bank_agent, 'id') else -2`
- Line 98: `if hasattr(target_agent, 'total_money_issued'):`
- Line 134: `if not hasattr(bank_agent, 'get_balance'):`
### `simulation/systems/lifecycle/adapters.py`
- Line 157: `return self._state.markets.get('stock') if hasattr(self._state, 'markets') else None`
- Line 203: `if bank and hasattr(bank, 'get_debt_status'):`
- Line 211: `if child and hasattr(child, '_bio_state') and getattr(child._bio_state, 'is_active', False):`
### `simulation/systems/lifecycle/birth_system.py`
- Line 48: `if not isinstance(context, IBirthContext):`
- Line 112: `if isinstance(parent_agent, ICurrencyHolder):`
- Line 191: `if hasattr(context.stock_market, 'update_shareholder'):`
### `simulation/agents/central_bank.py`
- Line 284: `if isinstance(amount, float):`
- Line 294: `if isinstance(amount, float):`
- Line 303: `if isinstance(amount, float):`
### `simulation/metrics/stock_tracker.py`
- Line 92: `if hasattr(firm.finance_state, "dividends_paid_last_tick"):`
- Line 272: `if hasattr(h._econ_state, "labor_income_this_tick"):`
- Line 277: `if hasattr(h._econ_state, "capital_income_this_tick"):`
### `simulation/factories/household_factory.py`
- Line 51: `if decision_engine and hasattr(decision_engine, 'value_orientation'):`
- Line 119: `if hasattr(agent, 'settlement_system'):`
### `simulation/decisions/base_decision_engine.py`
- Line 22: `assert hasattr(context, 'state') and context.state is not None, "Purity Error: context.state DTO is missing."`
- Line 23: `assert hasattr(context, 'config') and context.config is not None, "Purity Error: context.config DTO is missing."`
### `simulation/utils/golden_loader.py`
- Line 46: `if isinstance(data, dict):`
- Line 53: `elif isinstance(data, list):`
### `simulation/orchestration/phases_recovery.py`
- Line 33: `if isinstance(market, OrderBookMarket):`
- Line 37: `if self.world_state.public_manager and hasattr(self.world_state.public_manager, "managed_inventory"):`
### `simulation/orchestration/tick_orchestrator.py`
- Line 82: `if state.government and hasattr(state.government, "reset_tick_flow"):`
- Line 197: `if state.lifecycle_manager and hasattr(state.lifecycle_manager, "reset_agents_tick_state"):`
### `simulation/markets/circuit_breaker.py`
- Line 22: `if isinstance(price, float):`
- Line 30: `if isinstance(order.price_pennies, float):`
### `simulation/markets/matching_engine.py`
- Line 72: `agent_id = int(s_order.agent_id) if isinstance(s_order.agent_id, (int, float)) else s_order.agent_id`
- Line 223: `agent_id = int(s_order.agent_id) if isinstance(s_order.agent_id, (int, float)) else s_order.agent_id`
### `simulation/db/agent_repository.py`
- Line 23: `if isinstance(assets_val, dict):`
- Line 66: `if isinstance(assets_val, dict):`
### `simulation/ai/q_table_manager.py`
- Line 58: `action.name if isinstance(action, Enum) else str(action)`
- Line 96: `if (action_enum and isinstance(action_enum, type(Enum)))`
### `simulation/systems/technology_manager.py`
- Line 97: `if not isinstance(max_firm_id, int):`
- Line 257: `if hasattr(self.adoption_matrix, 'shape') and not hasattr(self.adoption_matrix.shape[0], '_mock_name'):`
### `simulation/systems/social_system.py`
- Line 17: `if hasattr(agent, "residing_property_id") and agent.residing_property_id is not None:`
- Line 19: `if hasattr(agent, "_econ_state") and agent._econ_state.residing_property_id is not None:`
### `simulation/systems/tax_agency.py`
- Line 92: `payer_id = payer.id if hasattr(payer, 'id') else str(payer)`
- Line 93: `payee_id = payee.id if hasattr(payee, 'id') else str(payee)`
### `simulation/systems/liquidation_handlers.py`
- Line 45: `if not (isinstance(agent, IInventoryHandler) and isinstance(agent, IConfigurable)):`
- Line 49: `if isinstance(self.public_manager, ILiquidator):`
### `simulation/systems/perception_system.py`
- Line 97: `if isinstance(val, (int, float)) and ("price" in key or "cost" in key):`
- Line 128: `if isinstance(val, (int, float)) and ("price" in key or "cost" in key):`
### `simulation/systems/liquidation_manager.py`
- Line 51: `if not isinstance(agent, ILiquidatable):`
- Line 217: `if hasattr(creditor, 'receive_repayment'):`
### `simulation/policies/smart_leviathan_policy.py`
- Line 54: `if isinstance(total_wealth, dict):`
### `simulation/viewmodels/economic_indicators_viewmodel.py`
- Line 116: `if isinstance(market, OrderBookMarket):`
### `simulation/interface/dashboard_connector.py`
- Line 100: `if hasattr(simulation.config_module, key):`
### `simulation/decisions/corporate_manager.py`
- Line 92: `if self.system2_planner and hasattr(self.system2_planner, 'cleanup'):`
### `simulation/decisions/standalone_rule_based_firm_engine.py`
- Line 38: `if not isinstance(firm, FirmStateDTO):`
### `simulation/utils/config_factory.py`
- Line 16: `if hasattr(config_module, config_key):`
### `simulation/components/market_component.py`
- Line 26: `if not hasattr(market, 'get_all_asks'):`
### `simulation/components/engines/sales_engine.py`
- Line 189: `if not hasattr(order, 'item_id') or not order.item_id:`
### `simulation/orchestration/phases/firm_operations.py`
- Line 28: `if state.tracker and hasattr(state.tracker, "capture_market_context"):`
### `simulation/orchestration/phases/politics.py`
- Line 26: `if not politics_system and hasattr(state, 'politics_system') and state.politics_system:`
### `simulation/orchestration/phases/bank_debt.py`
- Line 23: `if state.bank and hasattr(state.bank, "run_tick"):`
### `simulation/orchestration/phases/housing_saga.py`
- Line 31: `elif state.settlement_system and hasattr(state.settlement_system, 'process_sagas'):`
### `simulation/markets/market_circuit_breaker.py`
- Line 22: `if hasattr(self, '_last_update_tick') and self._last_update_tick == current_tick:`
### `simulation/markets/stock_market.py`
- Line 138: `if not isinstance(order, CanonicalOrderDTO):`
### `simulation/ai/state_builder.py`
- Line 26: `if "goods_market" in market_data and isinstance(`
### `simulation/ai/api.py`
- Line 126: `if isinstance(cash_data, dict):`
### `simulation/ai/service_firm_ai.py`
- Line 82: `if hasattr(firm_agent, "waste_this_tick") and hasattr(firm_agent, "capacity_this_tick"):`
### `simulation/ai/action_selector.py`
- Line 77: `if personality and best_actions and isinstance(best_actions[0], Intention):`
### `simulation/systems/sensory_system.py`
- Line 87: `if isinstance(h, ISensoryDataProvider):`
### `simulation/systems/ministry_of_education.py`
- Line 28: `if isinstance(government.revenue_this_tick, dict):`
### `simulation/systems/system_effects_manager.py`
- Line 88: `if isinstance(labor_config, dict):`
### `simulation/systems/handlers/emergency_handler.py`
- Line 36: `if isinstance(buyer, IInventoryHandler):`

## 3. Leaky Abstraction Candidates (Raw agent passed to DTO Context)
- No obvious leaky abstractions found (basic grep).

## 4. WorldState Purity Incursions (Services in WorldState)
- No obvious service instantiations found in WorldState.

## 5. Sacred Sequence Integrity
- Sacred sequence appears structurally intact.
