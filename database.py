import sqlite3
import random
import logging

logger = logging.getLogger(__name__)

def init_db():
    try:
        conn = sqlite3.connect("betsmilebot.db")
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'ru',
                demo_balance REAL DEFAULT 10.0,
                real_balance REAL DEFAULT 0.0,
                is_blocked INTEGER DEFAULT 0,
                referral_code TEXT,
                referred_by INTEGER,
                last_activity TIMESTAMP
            )
        """)
        
        # Таблица транзакций
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                amount REAL,
                type TEXT,
                status TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица игр
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                game_type TEXT,
                amount REAL,
                result TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    finally:
        conn.close()

def get_user(telegram_id):
    conn = sqlite3.connect("betsmilebot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_balance(telegram_id, demo_balance=None, real_balance=None):
    conn = sqlite3.connect("betsmilebot.db")
    cursor = conn.cursor()
    if demo_balance is not None:
        cursor.execute("UPDATE users SET demo_balance = ? WHERE telegram_id = ?", (demo_balance, telegram_id))
    if real_balance is not None:
        cursor.execute("UPDATE users SET real_balance = ? WHERE telegram_id = ?", (real_balance, telegram_id))
    cursor.execute("UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()

def add_user(telegram_id, referral_code=None):
    conn = sqlite3.connect("betsmilebot.db")
    cursor = conn.cursor()
    code = str(random.randint(100000, 999999)) if not referral_code else referral_code
    cursor.execute("INSERT OR IGNORE INTO users (telegram_id, referral_code) VALUES (?, ?)", (telegram_id, code))
    conn.commit()
    conn.close()
