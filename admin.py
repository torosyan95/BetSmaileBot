from aiogram import Dispatcher, types
from config import ADMIN_ID
from database import get_user
import sqlite3

def register_admin_handlers(dp: Dispatcher):
    @dp.message(commands=["admin"])
    async def admin_panel(message: types.Message):
        if message.from_user.id != ADMIN_ID:
            return
        conn = sqlite3.connect("betsmilebot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(amount) FROM​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​
