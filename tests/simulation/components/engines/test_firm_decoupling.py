import pytest
from modules.firm.api import (
    ProductionContextDTO, HRContextDTO, SalesContextDTO,
    ProductionIntentDTO, HRIntentDTO, SalesIntentDTO
)
from simulation.components.engines.production_engine import ProductionEngine
from simulation.components.engines.hr_engine import HREngine
from simulation.components.engines.sales_engine import SalesEngine
from modules.simulation.api import AgentID
from modules.system.api import MarketSnapshotDTO

def test_production_engine_decoupled():
    engine = ProductionEngine()
    context = ProductionContextDTO(
        firm_id=AgentID(1), tick=10, budget_pennies=10000, market_snapshot=MarketSnapshotDTO(10, {}, {}), available_cash_pennies=10000, is_solvent=True,
        inventory_raw_materials={'RAW': 100.0}, inventory_finished_goods={}, current_workforce_count=10,
        technology_level=1.0, production_efficiency=1.0, capital_stock=100.0, automation_level=0.0,
        input_goods={'RAW': 2.0}, output_good_id='WIDGET', labor_alpha=0.5, automation_labor_reduction=0.0,
        labor_elasticity_min=0.1, capital_depreciation_rate=0.01, specialization='WIDGET', base_quality=1.0,
        quality_sensitivity=0.5, employees_avg_skill=1.0
    )

    intent = engine.decide_production(context)

    assert intent.target_production_quantity > 0
    assert 'RAW' in intent.materials_to_use
    assert intent.materials_to_use['RAW'] == intent.target_production_quantity * 2.0
    assert intent.capital_depreciation > 0

def test_hr_engine_decoupled():
    engine = HREngine()
    # Scenario: Established firm (headcount=1) expanding to target (5)
    context = HRContextDTO(
        firm_id=AgentID(1), tick=10, budget_pennies=100000, market_snapshot=MarketSnapshotDTO(10, {}, {}), available_cash_pennies=100000, is_solvent=True,
        current_employees=[AgentID(1)], current_headcount=1, employee_wages={AgentID(1): 1000}, employee_skills={AgentID(1): 1.0},
        target_workforce_count=5, labor_market_avg_wage=1000, marginal_labor_productivity=1.0, happiness_avg=1.0,
        profit_history=[1000], min_employees=1, max_employees=100, severance_pay_weeks=2
    )

    intent = engine.decide_workforce(context)

    assert intent.hiring_target == 4 # Expanding from 1 to 5
    assert len(intent.fire_employee_ids) == 0

def test_sales_engine_decoupled():
    engine = SalesEngine()
    context = SalesContextDTO(
        firm_id=AgentID(1), tick=20, budget_pennies=0, market_snapshot=MarketSnapshotDTO(20, {}, {}), available_cash_pennies=0, is_solvent=True,
        inventory_to_sell={'WIDGET': 10.0}, current_prices={'WIDGET': 1000}, previous_sales_volume=0.0, competitor_prices={},
        marketing_budget_rate=0.05, brand_awareness=0.5, perceived_quality=1.0, inventory_quality={'WIDGET': 1.0},
        last_revenue_pennies=10000, last_marketing_spend_pennies=500, inventory_last_sale_tick={'WIDGET': 5},
        sale_timeout_ticks=10, dynamic_price_reduction_factor=0.9
    )

    intent = engine.decide_pricing(context)

    # 20 - 5 = 15 > 10 (timeout) -> Discount
    assert len(intent.sales_orders) == 1
    assert intent.sales_orders[0].item_id == 'WIDGET'
    assert intent.sales_orders[0].price_pennies < 1000
    assert 'WIDGET' in intent.price_adjustments

    # Marketing Budget
    # ROI: Revenue 10000 / Spend 500 = 20 > 2.0 -> Increase Rate (0.05 * 1.1)
    # Target = 10000 * (0.05*1.1) = 550
    # Smoothed = 500*0.8 + 550*0.2 = 400 + 110 = 510
    assert intent.marketing_spend_pennies > 0
    assert intent.marketing_spend_pennies == 510 # Or close to it
