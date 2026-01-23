import sqlite3
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "simulation_data.db"


def migrate():
    if not os.path.exists(DB_PATH):
        logger.error(f"Database file {DB_PATH} not found. Nothing to migrate.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Check agent_states table
    cursor.execute("PRAGMA table_info(agent_states)")
    columns = [row[1] for row in cursor.fetchall()]

    if "education_xp" not in columns:
        logger.info("Adding 'education_xp' to 'agent_states'...")
        cursor.execute(
            "ALTER TABLE agent_states ADD COLUMN education_xp REAL DEFAULT 0.0"
        )

    if "generation" not in columns:
        logger.info("Adding 'generation' to 'agent_states'...")
        cursor.execute(
            "ALTER TABLE agent_states ADD COLUMN generation INTEGER DEFAULT 0"
        )

    # 2. Check economic_indicators table
    cursor.execute("PRAGMA table_info(economic_indicators)")
    columns = [row[1] for row in cursor.fetchall()]

    if "avg_survival_need" not in columns:
        logger.info("Adding 'avg_survival_need' to 'economic_indicators'...")
        cursor.execute(
            "ALTER TABLE economic_indicators ADD COLUMN avg_survival_need REAL DEFAULT 0.0"
        )

    conn.commit()
    conn.close()
    logger.info("Migration completed successfully.")


if __name__ == "__main__":
    migrate()
