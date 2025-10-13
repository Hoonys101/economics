import os
import sys
import json

import config
from simulation.core_agents import Household, Talent, Personality
from simulation.ai_model import AIEngineRegistry
from simulation.core_markets import Market
from simulation.markets.order_book_market import OrderBookMarket
from simulation.decisions.action_proposal import ActionProposalEngine
from simulation.ai.state_builder import StateBuilder
from simulation.decisions.household_decision_engine import HouseholdDecisionEngine # Import HouseholdDecisionEngine

# 프로젝트 루트 경로를 sys.path에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def setup_test_environment():
    """테스트에 필요한 가상 환경을 설정합니다."""
    # 재화 데이터 로드
    try:
        with open("data/goods.json", 'r', encoding='utf-8') as f:
            goods_data = json.load(f)
    except FileNotFoundError:
        print("Error: goods.json not found. Make sure the file exists in the 'data' directory.")
        return None, None, None

    # 가상 시장 생성
    markets = {
        "goods_market": OrderBookMarket("goods_market"),
        "labor_market": OrderBookMarket("labor_market"),
        "loan_market": Market("loan_market") # Add loan_market
    }
    return goods_data, markets, None # all_households는 AI 결정에 직접 사용되지 않으므로 None

def test_ai_decision():
    """저장된 AI 모델을 불러와 가계의 의사결정을 테스트합니다."""
    print("--- Setting up test environment ---")
    goods_data, markets, _ = setup_test_environment()
    if not goods_data:
        return

    # 1. AI 의사결정 엔진 로드
    print("\n--- Loading AI Decision Engine ---")
    # 특정 가치관의 AI 모델을 불러옵니다.
    # 'wealth_and_needs'는 가장 기본적인 행동을 보일 것으로 예상됩니다.
    value_orientation = config.VALUE_ORIENTATION_WEALTH_AND_NEEDS
    action_proposal_engine = ActionProposalEngine(config_module=config, n_action_samples=10)
    state_builder = StateBuilder()
    # AIEngineRegistry를 모의(mock)하여 AIDecisionEngine 인스턴스를 반환하도록 설정
    ai_engine_registry = AIEngineRegistry(action_proposal_engine=action_proposal_engine, state_builder=state_builder)

    # HouseholdDecisionEngine 인스턴스 생성
    household_decision_engine = HouseholdDecisionEngine(agent_id=1, value_orientation=value_orientation, ai_engine_registry=ai_engine_registry)

    # 2. 테스트용 가계 에이전트 생성
    print("\n--- Creating Test Household Agent ---")
    talent = Talent(base_learning_rate=0.1, max_potential={"strength": 100})
    household = Household(
        id=1,
        talent=talent,
        goods_data=goods_data,
        initial_assets=50.0, # 강제 탐험 테스트를 위해 자산 임계치보다 낮게 설정
                    initial_needs={
                        "survival": 50.0,
                        "social": 20.0,
                        "improvement": 10.0,
                        "asset": 30.0,
                    },        value_orientation=value_orientation,
        decision_engine=household_decision_engine, # HouseholdDecisionEngine 인스턴스 전달
        personality=Personality.MISER,
        config_module=config
    )
    # HouseholdDecisionEngine에 Household 인스턴스 설정
    household_decision_engine.set_agent(household)

    # HouseholdDecisionEngine에 시장 정보 설정
    household_decision_engine.goods_market = markets['goods_market']
    household_decision_engine.labor_market = markets['labor_market']
    household_decision_engine.loan_market = markets['loan_market']

    print(f"Created Household {household.id} with Assets: {household.assets}, Needs: {household.needs}")

    # 3. AI 의사결정 테스트 실행
    print("\n--- Running AI Decision Simulation (10 ticks) ---")
    generated_orders = []
    for tick in range(10):
        print(f"\n[Tick {tick + 1}]")
        # make_decisions 호출에 필요한 market_data를 구성합니다.
        market_data = {
            "time": tick,
            "goods_market": {}, # 테스트에서는 단순화를 위해 비워둠
            "labor_market": {}, # 테스트에서는 단순화를 위해 비워둠
            "loan_market": None,
            "all_households": [],
            "goods_data": goods_data
        }
        orders, chosen_tactic = household.make_decision(markets, goods_data, market_data, tick)
        
        if orders:
            print(f"  > AI generated {len(orders)} order(s):")
            for order in orders:
                print(f"    - Type: {order.order_type}, Item: {order.item_id}, Qty: {order.quantity:.2f}, Price: {order.price:.2f}")
                generated_orders.append(order)
        else:
            print("  > AI generated no orders.")
            
        # 간단한 상태 업데이트 (자산만 변경)
        for order in orders:
            if order.order_type == 'BUY':
                household.assets -= order.quantity * order.price
            elif order.order_type == 'SELL':
                household.assets += order.quantity * order.price
        household.update_needs(tick) # 욕구 업데이트
        print(f"  > Updated Household State - Assets: {household.assets:.2f}, Survival Need: {household.needs['survival']:.1f}")


    # 4. 결과 분석
    print("\n\n--- Test Results Analysis ---")
    if not generated_orders:
        print("AI did not generate any transactions during the test.")
        return

    order_types = {"BUY": 0, "SELL": 0}
    item_ids = {}
    markets_used = {"goods_market": False, "labor_market": False}

    for order in generated_orders:
        order_types[order.order_type] += 1
        item_ids[order.item_id] = item_ids.get(order.item_id, 0) + 1
        if order.item_id == 'labor':
            markets_used['labor_market'] = True
        else:
            markets_used['goods_market'] = True

    print(f"Total orders generated: {len(generated_orders)}")
    print(f"Order type distribution: {order_types}")
    print(f"Traded item distribution: {item_ids}")
    print(f"Markets used: {markets_used}")

    print("\n--- Conclusion ---")
    if markets_used["goods_market"] and markets_used["labor_market"]:
        print("OK: The AI demonstrated transactions in both goods and labor markets.")
    else:
        print("WARN: The AI did not engage in transactions in all available markets.")

    if len(item_ids) > 1:
        print("OK: The AI attempted to trade more than one type of item.")
    else:
        print("WARN: The AI only traded one type of item.")
        
    if order_types["BUY"] > 0 and order_types["SELL"] > 0:
        print("OK: The AI demonstrated both BUY and SELL behaviors.")
    else:
        print("WARN: The AI only demonstrated one type of behavior (BUY or SELL).")


if __name__ == "__main__":
    test_ai_decision()
