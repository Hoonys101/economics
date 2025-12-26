# -*- coding: utf-8 -*-
import json
import random
import threading
import time
import logging
import os  # Import os
from flask import Flask, render_template, jsonify, request, g, Response
from functools import wraps
from typing import Callable, Any, Optional, cast

import config
from simulation.engine import Simulation
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.ai_model import AIEngineRegistry
from simulation.ai.api import Personality
from simulation.dtos import DecisionContext
from simulation.ai.state_builder import StateBuilder
from simulation.decisions.action_proposal import ActionProposalEngine
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.decisions.base_decision_engine import BaseDecisionEngine
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
simulation_lock = threading.Lock()

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
        household_decision_engine: Optional[BaseDecisionEngine] = None
        
        # Use EngineType enum for comparison
        if config.DEFAULT_ENGINE_TYPE == config.EngineType.AI_DRIVEN:
            ai_decision_engine = ai_manager.get_engine(value_orientation)
            household_ai = HouseholdAI(agent_id=str(i), ai_decision_engine=ai_decision_engine)
            household_decision_engine = AIDrivenHouseholdDecisionEngine(household_ai, config, logger)
        elif config.DEFAULT_ENGINE_TYPE == config.EngineType.RULE_BASED:
            household_decision_engine = RuleBasedHouseholdDecisionEngine(config, logger)
        else:
             # Default fallback
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
                    "survival": config.INITIAL_HOUSEHOLD_NEEDS_MEAN.get("survival", 60.0),
                    "asset": config.INITIAL_HOUSEHOLD_NEEDS_MEAN.get("asset", 10.0),
                    "social": config.INITIAL_HOUSEHOLD_NEEDS_MEAN.get("social", 20.0),
                    "improvement": config.INITIAL_HOUSEHOLD_NEEDS_MEAN.get("improvement", 10.0),
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
        firm_decision_engine: Optional[BaseDecisionEngine] = None
        
        # Use EngineType enum for comparison
        if config.DEFAULT_ENGINE_TYPE == config.EngineType.AI_DRIVEN:
            ai_decision_engine = ai_manager.get_engine(firm_value_orientation)
            firm_ai = FirmAI(agent_id=str(i + config.NUM_HOUSEHOLDS), ai_decision_engine=ai_decision_engine)
            firm_decision_engine = AIDrivenFirmDecisionEngine(firm_ai, config, logger)
        elif config.DEFAULT_ENGINE_TYPE == config.EngineType.RULE_BASED:
            firm_decision_engine = StandaloneRuleBasedFirmDecisionEngine(config, logger)
        else:
             # Default fallback
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
    # Note: In client-driven mode, "running" state is managed by the frontend.
    # Config changes will reset the simulation, so this is always safe.

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


@app.route("/api/simulation/tick", methods=["POST"])
@require_token
def advance_tick() -> Any:
    """Advance the simulation by one tick and return the update data."""
    if not simulation_instance:
        return cast(Response, jsonify({"status": "error", "message": "Simulation not initialized"})), 400

    start_time = time.time()
    current_tick = simulation_instance.time  # Get last known tick for error reporting

    try:
        with simulation_lock:
            simulation_instance.run_tick()
            current_tick = simulation_instance.time
        
        vm = EconomicIndicatorsViewModel(get_repository())
        latest_indicators = vm.get_economic_indicators(start_tick=current_tick)
        
        if not latest_indicators:
            return jsonify({"status": "error", "message": "No data generated for tick", "tick": current_tick}), 500

        latest_record = latest_indicators[-1]
        new_gdp_history = [latest_record.get("total_consumption", 0)]

        # --- Calculate Extended Metrics using ViewModel ---
        wealth_dist = vm.get_wealth_distribution(simulation_instance.households, simulation_instance.firms)
        needs_dist = vm.get_needs_distribution(simulation_instance.households, simulation_instance.firms)

        # For sales by good, we need recent transactions.
        # Ideally, we should pass transactions from this tick, but simulation_instance stores them in buffer or we can fetch from repo.
        # Since run_tick already flushed to DB (maybe), we can fetch from repository or rely on what's available.
        # Let's fetch recent transactions from repository for this tick.
        repo = get_repository()
        recent_txs = repo.get_transactions(start_tick=current_tick, end_tick=current_tick)
        sales_by_good = vm.get_sales_by_good(recent_txs)

        # Market Order Book
        open_orders = vm.get_market_order_book(simulation_instance.markets)

        # Calculate averages for dashboard cards
        hh_needs_avg = sum(needs_dist.get('household', {}).values()) / max(1, len(needs_dist.get('household', {})))
        firm_needs_avg = needs_dist.get('firm', {}).get('liquidity_need', 0)

        top_selling = max(sales_by_good, key=sales_by_good.get) if sales_by_good else "None"

        update_data = {
            "status": "running",
            "tick": current_tick,
            "gdp": latest_record.get("total_consumption", 0),
            "population": latest_record.get("population", config.NUM_HOUSEHOLDS),
            "unemployment_rate": latest_record.get("unemployment_rate", 0),
            "trade_volume": sum(sales_by_good.values()), # Total trade volume for this tick
            "top_selling_good": top_selling,
            "average_household_wealth": latest_record.get("total_household_assets", 0)
            / latest_record.get("population", 1),
            "average_firm_wealth": latest_record.get("total_firm_assets", 0)
            / config.NUM_FIRMS,
            "household_avg_needs": hh_needs_avg,
            "firm_avg_needs": firm_needs_avg,
            "chart_update": {
                "new_gdp_history": new_gdp_history,
                "wealth_distribution": wealth_dist,
                "household_needs_distribution": needs_dist['household'],
                "firm_needs_distribution": needs_dist['firm'],
                "sales_by_good": sales_by_good
            },
            "market_update": {
                "open_orders": open_orders,
                "transactions": recent_txs # Also send transactions for the list
            },
            "duration_ms": (time.time() - start_time) * 1000
        }
        
        return jsonify(update_data)

    except Exception as e:
        logging.exception(f"Error during tick {current_tick}: {e}")
        # Attempt to flush any buffered data before returning error
        try:
            if simulation_instance:
                simulation_instance._flush_buffers_to_db()
        except Exception:
            pass  # Best effort
        return jsonify({
            "status": "error",
            "message": str(e),
            "tick": current_tick
        }), 500


@app.route("/api/simulation/start", methods=["POST"])
@require_token
def start_simulation():
    # Only useful for logging or backend state tracking if needed
    # But for client-driven, this is mostly a placeholder or can be removed.
    # We kept it to satisfy the button calls in frontend (initially), 
    # but we will change frontend to not call these for logic control, 
    # EXCEPT maybe for explicit logging?
    # Let's keep it simple: Just return success, maybe log.
    logging.info("Simulation start requested (Client-driven mode)")
    return jsonify({"status": "success", "message": "Simulation start acknowledged."})


@app.route("/api/simulation/pause", methods=["POST"])
@require_token
def pause_simulation():
    logging.info("Simulation pause requested (Client-driven mode)")
    return jsonify({"status": "success", "message": "Simulation paused."})


@app.route("/api/simulation/stop", methods=["POST"])
@require_token
def stop_simulation():
    global simulation_instance
    simulation_instance = None
    logging.info("Simulation stopped and instance cleared.")
    return jsonify({"status": "success", "message": "Simulation stopped."})


@app.route("/api/simulation/reset", methods=["POST"])
@require_token
def reset_simulation():
    global simulation_instance
    with simulation_lock:
        # Finalize the old instance before creating a new one
        if simulation_instance:
            try:
                simulation_instance.finalize_simulation()
            except Exception as e:
                logging.warning(f"Error finalizing old simulation: {e}")
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
