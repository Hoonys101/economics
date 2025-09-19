import sqlite3

def create_tables(conn: sqlite3.Connection):
    """
    SQLite3 데이터베이스에 필요한 테이블을 생성합니다.
    """
    cursor = conn.cursor()

    # Transaction 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time INTEGER NOT NULL,
            buyer_id INTEGER NOT NULL,
            seller_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            market_id TEXT NOT NULL,
            transaction_type TEXT NOT NULL
        )
    ''')

    # AgentState 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            num_employees INTEGER
        )
    ''')

    # MarketHistory 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time INTEGER NOT NULL,
            market_id TEXT NOT NULL,
            item_id TEXT,
            avg_price REAL,
            trade_volume REAL,
            best_ask REAL,
            best_bid REAL
        )
    ''')

    # EconomicIndicator 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS economic_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time INTEGER NOT NULL,
            unemployment_rate REAL,
            avg_wage REAL,
            food_avg_price REAL,
            avg_goods_price REAL,
            total_production REAL,
            total_consumption REAL,
            total_household_assets REAL,
            total_firm_assets REAL,
            total_food_consumption REAL,
            total_inventory REAL
        )
    ''')

    conn.commit()

if __name__ == '__main__':
    # 테스트용 데이터베이스 생성 및 테이블 확인
    conn = sqlite3.connect('test_simulation.db')
    create_tables(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print("Created tables:", cursor.fetchall())
    conn.close()