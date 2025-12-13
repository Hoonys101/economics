# -*- coding: utf-8 -*-
import json
import random
import threading
import time
import logging
import os  # Import os
from flask import Flask, render_template, jsonify, request, g, Response
from functools import wraps
from typing import Callable, Any

import config
from simulation.engine import Simulation
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.ai_model import AIEngineRegistry
from simulation.ai.api import Personality
from simulation.ai.state_builder import StateBuilder
from simulation.decisions.action_proposal import ActionProposalEngine
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.decisions.ai_driven_household_engine import (
    AIDrivenHouseholdDecisionEngine,
)
from simulation.decisions.rule_based_household_engine import RuleBasedHouseholdDecisionEngine
from simulation.decisions.standalone_rule_based_firm_engine import StandaloneRuleBasedFirmDecisionEngine
from simulation.ai.household_ai import HouseholdAI
from simulation.ai.firm_ai import FirmAI

# Import ViewModels
from simulation.db.repository import SimulationRepository
from simulation.viewmodels.economic_indicators_viewmodel import (
    EconomicIndicatorsViewModel,
)
from simulation.viewmodels.market_history_viewmodel import MarketHistoryViewModel
from simulation.viewmodels.agent_state_viewmodel import AgentStateViewModel

logger = logging.getLogger(__name__)

# ==============================================
# Global Variables & Locks
# ==============================================
app = Flask(__name__)
simulation_instance: Simulation | None = None
simulation_thread: threading.Thread | None = None
simulation_lock = threading.Lock()

# 시뮬레이션 실행 상태를 제어하는 플래그
simulation_running = threading.Event()

state_builder = StateBuilder()
action_proposal_engine = ActionProposalEngine(config_module=config)
ai_manager = AIEngineRegistry(
    action_proposal_engine=action_proposal_engine, state_builder=state_builder
)  # AI Training Manager 인스턴스 생성


# ==============================================
# Authentication
# ==============================================
def require_token(f: Callable) -> Callable:
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> tuple[Response, int] | Response:
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]
        if not token:
            return jsonify({"message": "Token is missing!"}), 401
        if token != config.SECRET_TOKEN:
            return jsonify({"message": "Token is invalid!"}), 401
        return f(*args, **kwargs)

    return decorated


# ==============================================
# Database Connection Management (Per-request)
# ==============================================


def get_repository() -> SimulationRepository:
    if "_repository_instance" not in g:
        g._repository_instance = SimulationRepository()
    return g._repository_instance





# ==============================================
# Simulation Setup
# ==============================================


def create_simulation() -> None:
    """`config`와 `goods.json`을 기반으로 새로운 시뮬레이션 인스턴스를 생성하고 반환합니다."""
    global simulation_instance

    # Create a new repository instance for each simulation
    repository = SimulationRepository()

    try:
        with open("data/goods.json", "r", encoding="utf-8") as f:
            goods_data = json.load(f)
    except FileNotFoundError:
        logging.error(
            "Error: data/goods.json not found!",
            extra={
                "tick": 0,
                "agent_type": "App",
                "agent_id": 0,
                "method_name": "create_simulation",
                "tags": ["app_error"],
            },
        )
        return

    all_value_orientations = [
        config.VALUE_ORIENTATION_WEALTH_AND_NEEDS,
        config.VALUE_ORIENTATION_NEEDS_AND_GROWTH,
        config.VALUE_ORIENTATION_NEEDS_AND_SOCIAL_STATUS,
    ]

    households = []
    for i in range(config.NUM_HOUSEHOLDS):
        value_orientation = random.choice(all_value_orientations)
        household_decision_engine = None
        if config.DEFAULT_ENGINE_TYPE == "AIDriven":
            ai_decision_engine = ai_manager.get_engine(value_orientation)
            household_ai = HouseholdAI(agent_id=str(i), ai_decision_engine=ai_decision_engine)
            household_decision_engine = AIDrivenHouseholdDecisionEngine(household_ai, config, logger)
        elif config.DEFAULT_ENGINE_TYPE == "RuleBased":
            household_decision_engine = RuleBasedHouseholdDecisionEngine(config, logger)
        else:
            # Default to AIDriven if an unknown type is specified
            ai_decision_engine = ai_manager.get_engine(value_orientation)
            household_ai = HouseholdAI(agent_id=str(i), ai_decision_engine=ai_decision_engine)
            household_decision_engine = AIDrivenHouseholdDecisionEngine(household_ai, config, logger)
            logger.warning(f"Unknown DEFAULT_ENGINE_TYPE '{config.DEFAULT_ENGINE_TYPE}' specified. Using AIDriven engine.")

        households.append(
            Household(
                id=i,
                talent=Talent(1.0, {}),
                goods_data=goods_data,
                initial_assets=config.INITIAL_HOUSEHOLD_ASSETS_MEAN,
                initial_needs={
                    "survival_need": config.INITIAL_HOUSEHOLD_NEEDS_MEAN[
                        "survival_need"
                    ],
                    "recognition_need": config.INITIAL_HOUSEHOLD_NEEDS_MEAN[
                        "recognition_need"
                    ],
                    "growth_need": config.INITIAL_HOUSEHOLD_NEEDS_MEAN["growth_need"],
                    "wealth_need": config.INITIAL_HOUSEHOLD_NEEDS_MEAN["wealth_need"],
                    "imitation_need": config.INITIAL_HOUSEHOLD_NEEDS_MEAN[
                        "imitation_need"
                    ],
                    "labor_need": config.INITIAL_HOUSEHOLD_NEEDS_MEAN.get(
                        "labor_need", 0.0
                    ),
                    "liquidity_need": config.INITIAL_HOUSEHOLD_LIQUIDITY_NEED_MEAN,
                },
                decision_engine=household_decision_engine,
                value_orientation=value_orientation,
                personality=random.choice(list(Personality)),  # Add personality
                logger=logger,
                config_module=config,
            )
        )

    firms = []
    for i in range(config.NUM_FIRMS):
        firm_value_orientation = random.choice(all_value_orientations)
        firm_decision_engine = None
        if config.DEFAULT_ENGINE_TYPE == "AIDriven":
            ai_decision_engine = ai_manager.get_engine(firm_value_orientation)
            firm_ai = FirmAI(agent_id=str(i + config.NUM_HOUSEHOLDS), ai_decision_engine=ai_decision_engine)
            firm_decision_engine = AIDrivenFirmDecisionEngine(firm_ai, config, logger)
        elif config.DEFAULT_ENGINE_TYPE == "RuleBased":
            firm_decision_engine = StandaloneRuleBasedFirmDecisionEngine(config, logger)
        else:
            # Default to AIDriven if an unknown type is specified
            ai_decision_engine = ai_manager.get_engine(firm_value_orientation)
            firm_ai = FirmAI(agent_id=str(i + config.NUM_HOUSEHOLDS), ai_decision_engine=ai_decision_engine)
            firm_decision_engine = AIDrivenFirmDecisionEngine(firm_ai, config, logger)
            logger.warning(f"Unknown DEFAULT_ENGINE_TYPE '{config.DEFAULT_ENGINE_TYPE}' specified. Using AIDriven engine.")
        firms.append(
            Firm(
                id=i + config.NUM_HOUSEHOLDS,
                initial_capital=config.INITIAL_FIRM_CAPITAL_MEAN,
                initial_liquidity_need=config.INITIAL_FIRM_LIQUIDITY_NEED_MEAN,
                specialization=config.FIRM_SPECIALIZATIONS[i],
                productivity_factor=config.FIRM_PRODUCTIVITY_FACTOR,
                decision_engine=firm_decision_engine,
                value_orientation=firm_value_orientation,
                config_module=config,  # Add config_module
                logger=logger,
            )
        )

    simulation_instance = Simulation(
        households=households,
        firms=firms,
        ai_trainer=ai_manager,
        repository=repository,
        config_module=config,
        goods_data=goods_data,
        logger=logger,
    )
    logging.info(
        "New simulation instance created.",
        extra={
            "tick": 0,
            "agent_type": "App",
            "agent_id": 0,
            "method_name": "create_simulation",
            "tags": ["app_info"],
        },
    )


# ==============================================
# Background Simulation Thread
# ==============================================


def run_simulation_loop() -> None:
    """시뮬레이션 루프를 실행하는 백그라운드 스레드의 타겟 함수"""
    try:
        while simulation_running.is_set():
            with simulation_lock:
                if simulation_instance:
                    simulation_instance.run_tick()
            time.sleep(0.1)
        logging.info(
            "Simulation loop stopped.",
            extra={
                "tick": simulation_instance.time if simulation_instance else 0,
                "agent_type": "App",
                "agent_id": 0,
                "method_name": "run_simulation_loop",
                "tags": ["app_info"],
            },
        )
    finally:
        pass


# ==============================================
# HTML Page Rendering
# ==============================================
@app.route("/")
def index() -> str:
    return render_template("index.html")


# ==============================================
# API Endpoints (Now connected to the engine)
# ==============================================


@app.route("/api/config", methods=["GET"])
def get_config() -> Response:
    config_vars = {
        k: v
        for k, v in dict(config.__dict__).items()
        if not k.startswith("__") and isinstance(v, (int, float, str, dict))
    }
    return jsonify(config_vars)


@app.route("/api/config", methods=["POST"])
@require_token
def set_config() -> tuple[Response, int] | Response:
    if simulation_running.is_set():
        return jsonify(
            {
                "status": "error",
                "message": "Cannot change settings while simulation is running.",
            }
        ), 400

    new_config = request.json
    if new_config is None:
        return jsonify({"status": "error", "message": "Invalid JSON in request body."}), 400
    with simulation_lock:
        for key, value in new_config.items():
            if hasattr(config, key):
                try:
                    original_type = type(getattr(config, key))
                    setattr(config, key, original_type(value))
                except (ValueError, TypeError):
                    return jsonify(
                        {"status": "error", "message": f"Invalid value for {key}"}
                    ), 400
        create_simulation()
    return jsonify(
        {"status": "success", "message": "Configuration updated and simulation reset."}
    )


# --- GEMINI_TEMP_CHANGE_START: New API Endpoints for data access ---
@app.route("/api/economic_indicators", methods=["GET"])
def get_economic_indicators_api() -> Response:
    start_tick = request.args.get("start_tick", type=int)
    end_tick = request.args.get("end_tick", type=int)
    vm = EconomicIndicatorsViewModel(get_repository())

    data = vm.get_economic_indicators(start_tick, end_tick)
    return jsonify(data)


@app.route("/api/market_history/<market_id>", methods=["GET"])
def get_market_history_api(market_id: str) -> Response:
    start_tick = request.args.get("start_tick", type=int)
    end_tick = request.args.get("end_tick", type=int)
    item_id = request.args.get("item_id", type=str)

    vm = MarketHistoryViewModel(
        get_repository()
    )  # Use get_repository() to create a new instance
    data = vm.get_market_history(market_id, start_tick, end_tick, item_id)
    return jsonify(data)


@app.route("/api/agent_state/<int:agent_id>", methods=["GET"])
def get_agent_state_api(agent_id: int) -> Response:
    start_tick = request.args.get("start_tick", type=int)
    end_tick = request.args.get("end_tick", type=int)

    vm = AgentStateViewModel(get_repository())
    data = vm.get_agent_states(agent_id, start_tick, end_tick)
    return jsonify(data)


@app.route("/api/market/transactions", methods=["GET"])
def get_transactions_api() -> Response:
    """최신 거래 내역을 반환하는 API 엔드포인트"""
    since_tick = request.args.get("since", 0, type=int)

    repo = get_repository()
    transactions = repo.get_transactions(start_tick=since_tick)
    return jsonify(transactions)


# --- GEMINI_TEMP_CHANGE_END ---


@app.route("/api/simulation/update", methods=["GET"])
def get_simulation_update():
    """UI 업데이트에 필요한 최소한의 데이터를 DB에서 조회하여 반환합니다."""
    since_tick = request.args.get("since", 0, type=int)

    vm = EconomicIndicatorsViewModel(get_repository())
    latest_indicators = vm.get_economic_indicators(start_tick=since_tick)

    if not latest_indicators:
        with simulation_lock:
            current_tick = simulation_instance.time if simulation_instance else 0
            if current_tick == since_tick:
                return jsonify({"status": "no_update"})
            return jsonify(
                {
                    "status": "running" if simulation_running.is_set() else "paused",
                    "tick": current_tick,
                }
            )

    current_tick = latest_indicators[-1]["time"]
    latest_record = latest_indicators[-1]

    new_gdp_history = [r.get("total_consumption", 0) for r in latest_indicators]

    update_data = {
        "status": "running" if simulation_running.is_set() else "paused",
        "tick": current_tick,
        "gdp": latest_record.get("total_consumption", 0),
        "population": latest_record.get("population", config.NUM_HOUSEHOLDS),
        "unemployment_rate": latest_record.get("unemployment_rate", 0),
        "trade_volume": latest_record.get("total_trade_volume", 0),
        "top_selling_good": "N/A",
        "average_household_wealth": latest_record.get("total_household_assets", 0)
        / latest_record.get("population", 1),
        "average_firm_wealth": latest_record.get("total_firm_assets", 0)
        / config.NUM_FIRMS,
        "household_avg_needs": 0,
        "firm_avg_needs": 0,
        "chart_update": {
            "new_gdp_history": new_gdp_history,
            "wealth_distribution": [],
            "household_needs_distribution": {},
        },
        "market_update": {"open_orders": [], "transactions": []},
    }
    return jsonify(update_data)


@app.route("/api/simulation/start", methods=["POST"])
@require_token
def start_simulation():
    global simulation_thread
    if not simulation_running.is_set():
        simulation_running.set()
        if not simulation_thread or not simulation_thread.is_alive():
            simulation_thread = threading.Thread(target=run_simulation_loop)
            simulation_thread.start()
        return jsonify({"status": "success", "message": "Simulation started."})
    return jsonify({"status": "already_running"})


@app.route("/api/simulation/pause", methods=["POST"])
@require_token
def pause_simulation():
    simulation_running.clear()
    return jsonify({"status": "success", "message": "Simulation paused."})


@app.route("/api/simulation/stop", methods=["POST"])
@require_token
def stop_simulation():
    global simulation_thread, simulation_instance
    simulation_running.clear()
    if simulation_thread and simulation_thread.is_alive():
        time.sleep(0.2)
    simulation_thread = None
    simulation_instance = None
    logging.info(
        "Simulation stopped and instance cleared.",
        extra={
            "tick": 0,
            "agent_type": "App",
            "agent_id": 0,
            "method_name": "stop_simulation",
            "tags": ["app_info"],
        },
    )
    return jsonify({"status": "success", "message": "Simulation stopped."})


@app.route("/api/simulation/reset", methods=["POST"])
@require_token
def reset_simulation():
    global simulation_thread
    simulation_running.clear()
    simulation_thread = None

    with simulation_lock:
        create_simulation()

    return jsonify({"status": "success", "message": "Simulation reset."})


@app.route("/api/simulation/shutdown", methods=["POST"])
@require_token
def shutdown_server():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        logger.warning(
            "Attempted to shut down server, but not running with Werkzeug development server.",
            extra={"tags": ["app_shutdown"]},
        )
        return jsonify(
            {
                "status": "error",
                "message": "Server is not running in a development environment or Werkzeug server.",
            }
        ), 500
    try:
        func()
        logger.info("Server shutting down...", extra={"tags": ["app_shutdown"]})
        return jsonify({"status": "success", "message": "Server shutting down..."})
    except Exception as e:
        logger.error(
            f"Error during server shutdown: {e}", extra={"tags": ["app_shutdown"]}
        )
        return jsonify(
            {"status": "error", "message": f"Error during server shutdown: {e}"}
        ), 500


# 앱 시작 시 시뮬레이션 초기화
if __name__ == "__main__":
    create_simulation()
    import cProfile
    import pstats

    profiler = cProfile.Profile()
    profiler.enable()

    try:
        app.run(debug=True, port=5001, use_reloader=False)
    finally:
        profiler.disable()
        stats = pstats.Stats(profiler).sort_stats("cumtime")
        stats.print_stats(20)
        profile_path = os.path.join(os.path.dirname(__file__), "app_profile.prof")
        stats.dump_stats(profile_path)
        logging.info(f"Profiling data saved to {profile_path}")
