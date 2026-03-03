import psycopg2
from config import DATABASE_URL

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id SERIAL PRIMARY KEY,
        token_name TEXT,
        mcap FLOAT,
        description TEXT,
        telegram TEXT,
        website TEXT,
        pitch TEXT,
        status TEXT DEFAULT 'available'
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS reps (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE,
        active_lead_id INTEGER
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
