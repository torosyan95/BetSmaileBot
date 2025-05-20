from aiogram import Dispatcher, types
from aiogram.filters import Command
from config import ADMIN_ID
from database import get_user
import sqlite3

def register_admin_handlers(dp: Dispatcher):
    @dp.message(Command("admin"))
    async def admin_panel(message: types.Message):
        if message.from_user.id != ADMIN_ID:
            return
        conn = sqlite3.connect("betsmilebot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'deposit' AND status = 'completed'")
        total_deposits = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'withdraw' AND status = 'pending'")
        pending_withdrawals = cursor.fetchone()[0] or 0
        conn.close()
        
        text = f"📊 Admin Panel\nUsers: {user_count}\nTotal Deposits: ${total_deposits}\nPending Withdrawals: ${pending_withdrawals}"
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="View Users", callback_data="admin_users"),
             types.InlineKeyboardButton(text="Pending Withdrawals", callback_data="admin_withdrawals")]
        ])
        await message.answer(text, reply_markup=keyboard)

    @dp.callback_query(lambda c: c.data == "admin_users")
    async def admin_users(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            return
        conn = sqlite3.connect("betsmilebot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id, real_balance FROM users LIMIT 5")
        users = cursor.fetchall()
        conn.close()
        text = "👥 Users:\n" + "\n".join([f"ID: {u[0]}, Balance: ${u[1]}" for u in users])
        await callback.message.edit_text(text)

    @dp.callback_query(lambda c: c.data == "admin_withdrawals")
    async def admin_withdrawals(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            return
        conn = sqlite3.connect("betsmilebot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id, amount FROM transactions WHERE type = 'withdraw' AND status = 'pending' LIMIT 5")
        withdrawals = cursor.fetchall()
        conn.close()
        text = "📤 Pending Withdrawals:\n" + "\n".join([f"ID: {w[0]}, Amount: ${w[1]}" for w in withdrawals])
        await callback.message.edit_text(text)
