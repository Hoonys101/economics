import sqlite3
import logging


def create_tables(conn: sqlite3.Connection):
    """
    SQLite3 데이터베이스에 필요한 테이블을 생성합니다.
    """
    cursor = conn.cursor()

    # Simulation Runs 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS simulation_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            description TEXT,
            config_hash TEXT NOT NULL
        )
    """)

    # Transaction 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            time INTEGER NOT NULL,
            buyer_id INTEGER NOT NULL,
            seller_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            market_id TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES simulation_runs (run_id)
        )
    """)

    # AgentState 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            time INTEGER NOT NULL,
            agent_id INTEGER NOT NULL,
            agent_type TEXT NOT NULL,
            assets REAL NOT NULL,
            is_active BOOLEAN NOT NULL,
            is_employed BOOLEAN,
            employer_id INTEGER,
            needs_survival REAL,
            needs_labor REAL,
            inventory_food REAL,
            current_production REAL,
            num_employees INTEGER,
            education_xp REAL,
            generation INTEGER,
            FOREIGN KEY (run_id) REFERENCES simulation_runs (run_id)
        )
    """)

    # MarketHistory 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time INTEGER NOT NULL,
            market_id TEXT NOT NULL,
            item_id TEXT,
            avg_price REAL,
            trade_volume REAL,
            best_ask REAL,
            best_bid REAL,
            avg_ask REAL,
            avg_bid REAL,
            worst_ask REAL,
            worst_bid REAL
        )
    """)

    # EconomicIndicator 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS economic_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            time INTEGER NOT NULL,
            unemployment_rate REAL,
            avg_wage REAL,
            food_avg_price REAL,
            food_trade_volume REAL,
            avg_goods_price REAL,
            total_production REAL,
            total_consumption REAL,
            total_household_assets REAL,
            total_firm_assets REAL,
            total_food_consumption REAL,
            total_inventory REAL,
            avg_survival_need REAL,
            total_labor_income REAL,
            total_capital_income REAL,
            FOREIGN KEY (run_id) REFERENCES simulation_runs (run_id)
        )
    """)

    # AI Decisions History 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_decisions_history (
            decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            tick INTEGER NOT NULL,
            agent_id INTEGER NOT NULL,
            decision_type TEXT NOT NULL,
            decision_details TEXT,
            predicted_reward REAL,
            actual_reward REAL,
            FOREIGN KEY (run_id) REFERENCES simulation_runs (run_id)
        )
    """)

    # Stock Market History 테이블 (기업별 주가 이력)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_market_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            time INTEGER NOT NULL,
            firm_id INTEGER NOT NULL,
            stock_price REAL,
            book_value_per_share REAL,
            price_to_book_ratio REAL,
            trade_volume REAL,
            buy_order_count INTEGER,
            sell_order_count INTEGER,
            firm_assets REAL,
            firm_profit REAL,
            dividend_paid REAL,
            market_cap REAL,
            FOREIGN KEY (run_id) REFERENCES simulation_runs (run_id)
        )
    """)

    # Wealth Distribution 테이블 (불평등 지표)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wealth_distribution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            time INTEGER NOT NULL,
            gini_total_assets REAL,
            gini_financial_assets REAL,
            gini_stock_holdings REAL,
            labor_income_share REAL,
            capital_income_share REAL,
            top_10_pct_wealth_share REAL,
            bottom_50_pct_wealth_share REAL,
            mean_household_assets REAL,
            median_household_assets REAL,
            mean_to_median_ratio REAL,
            FOREIGN KEY (run_id) REFERENCES simulation_runs (run_id)
        )
    """)

    # Household Income 테이블 (가계별 소득 원천)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS household_income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            time INTEGER NOT NULL,
            household_id INTEGER NOT NULL,
            labor_income REAL,
            dividend_income REAL,
            capital_gains REAL,
            total_income REAL,
            portfolio_value REAL,
            portfolio_return_rate REAL,
            FOREIGN KEY (run_id) REFERENCES simulation_runs (run_id)
        )
    """)

    # Social Mobility 테이블 (계층 이동 지표)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS social_mobility (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            time INTEGER NOT NULL,
            quintile_1_count INTEGER,
            quintile_2_count INTEGER,
            quintile_3_count INTEGER,
            quintile_4_count INTEGER,
            quintile_5_count INTEGER,
            upward_mobility_count INTEGER,
            downward_mobility_count INTEGER,
            stable_count INTEGER,
            quintile_1_avg_assets REAL,
            quintile_2_avg_assets REAL,
            quintile_3_avg_assets REAL,
            quintile_4_avg_assets REAL,
            quintile_5_avg_assets REAL,
            mobility_index REAL,
            FOREIGN KEY (run_id) REFERENCES simulation_runs (run_id)
        )
    """)

    # Personality Statistics 테이블 (성향별 통계)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personality_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            time INTEGER NOT NULL,
            personality_type TEXT NOT NULL,
            count INTEGER,
            avg_assets REAL,
            median_assets REAL,
            avg_labor_income REAL,
            avg_capital_income REAL,
            labor_income_ratio REAL,
            employment_rate REAL,
            avg_portfolio_value REAL,
            avg_stock_holdings REAL,
            avg_survival_need REAL,
            avg_social_need REAL,
            avg_improvement_need REAL,
            avg_wealth_growth_rate REAL,
            FOREIGN KEY (run_id) REFERENCES simulation_runs (run_id)
        )
    """)

    # Agent Thoughts 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_thoughts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            tick INTEGER,
            agent_id TEXT,
            action_type TEXT,
            decision TEXT,
            reason TEXT,
            context_data JSON
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_thoughts_tick ON agent_thoughts(tick)")

    # Tick Snapshots 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tick_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            run_id INTEGER,
            gdp REAL,
            m2 REAL,
            cpi REAL,
            transaction_count INTEGER
        )
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_economic_indicators_time ON economic_indicators(time)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_time ON transactions(time)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_states_time ON agent_states(time)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_history_time ON market_history(time)")

    conn.commit()



if __name__ == "__main__":
    # 테스트용 데이터베이스 생성 및 테이블 확인
    conn = sqlite3.connect("test_simulation.db")
    create_tables(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    logging.info(f"Created tables: {cursor.fetchall()}")
    conn.close()
