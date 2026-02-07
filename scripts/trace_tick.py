
import sys
import os
sys.path.append(os.getcwd())
from main import create_simulation
import logging

def trace_tick():
    sim = create_simulation()
    state = sim.world_state
    
    def report(name):
        money = state.calculate_total_money()
        total_usd = money.get("USD", 0.0) if isinstance(money, dict) else money
        print(f"[{name}] Total: {total_usd:,.2f}")
        return money

    print("--- TICK TRACE START ---")
    m0 = report("Baseline")
    
    # Simulate phases manually to find where it jumps
    # 1. Monetery Baseline (not needed)
    
    # 2. Production
    for firm in state.firms:
         if firm.is_active:
             firm.produce(state.time, technology_manager=state.technology_manager)
    report("Post-Production")
    
    # 3. System Transactions
    market_data_prev = sim.tick_scheduler.prepare_market_data(state.tracker)
    system_transactions = []
    
    # Bank
    if hasattr(state.bank, "run_tick"):
         bank_txs = state.bank.run_tick(state.agents, state.time)
         system_transactions.extend(bank_txs)
    report("Post-Bank-Tick")
    
    # Firm Financials
    market_context = sim.tick_scheduler.get_market_context(state.tracker) if hasattr(sim.tick_scheduler, "get_market_context") else None
    if not market_context:
         market_context = {"exchange_rates": {"USD": 1.0}, "benchmark_rates": {}}

    for firm in state.firms:
         if firm.is_active:
             system_transactions.extend(firm.generate_transactions(
                 government=state.government,
                 market_data=market_data_prev,
                 shareholder_registry=state.shareholder_registry,
                 current_time=state.time,
                 market_context=market_context
             ))
    report("Post-Firm-Gen")
    
    # Welfare
    system_transactions.extend(state.government.run_welfare_check(list(state.agents.values()), market_data_prev, state.time))
    report("Post-Welfare-Gen")
    
    # Infrastructure
    infra = state.government.invest_infrastructure(state.time, state.households)
    if infra: system_transactions.extend(infra)
    report("Post-Infra-Gen")
    
    # Education
    edu = state.government.run_public_education(state.households, state.config_module, state.time)
    if edu: system_transactions.extend(edu)
    report("Post-Edu-Gen")
    
    # Transaction Execution
    if state.transaction_processor:
        # Simulate local list for simplicity
        from simulation.dtos.api import SimulationState
        sim_state = SimulationState(
            time=state.time, households=state.households, firms=state.firms,
            agents=state.agents, markets=state.markets, government=state.government,
            bank=state.bank, central_bank=state.central_bank,
            transactions=system_transactions, config_module=state.config_module,
            tracker=state.tracker, logger=state.logger, goods_data=state.goods_data,
            next_agent_id=state.next_agent_id, real_estate_units=state.real_estate_units,
            settlement_system=state.settlement_system, inactive_agents=state.inactive_agents,
            ai_training_manager=state.ai_training_manager,
            ai_trainer=state.ai_trainer,
            stock_market=state.stock_market,
            stock_tracker=state.stock_tracker,
            market_data={}
        )
        state.transaction_processor.execute(sim_state)
    report("Post-Execution")
    
    # Housing System
    state.housing_system.process_housing(state)
    state.housing_system.apply_homeless_penalty(state)
    report("Post-Housing")
    
    # Lifecycle
    if state.lifecycle_manager:
        from simulation.dtos.api import SimulationState
        sim_state = SimulationState(
            time=state.time, households=state.households, firms=state.firms,
            agents=state.agents, markets=state.markets, government=state.government,
            bank=state.bank, central_bank=state.central_bank,
            transactions=[], config_module=state.config_module,
            tracker=state.tracker, logger=state.logger, goods_data=state.goods_data,
            next_agent_id=state.next_agent_id, real_estate_units=state.real_estate_units,
            settlement_system=state.settlement_system, inactive_agents=state.inactive_agents,
            ai_training_manager=state.ai_training_manager,
            ai_trainer=state.ai_trainer,
            stock_market=state.stock_market,
            stock_tracker=state.stock_tracker,
            market_data={}
        )
        state.lifecycle_manager.execute(sim_state)
    report("Post-Lifecycle")
    

if __name__ == "__main__":
    trace_tick()
