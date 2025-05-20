from aiogram import Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user, update_balance, add_user
from games import play_game
from payments import create_payment
from utils import get_text, ANIMATION_GIFS
import random
import asyncio
import time

class GameStates(StatesGroup):
    SELECT_GAME = State()
    ENTER_AMOUNT = State()
    AGE_CONFIRM = State()

def register_handlers(dp: Dispatcher):
    @dp.message(commands=["start"])
    async def start_command(message: types.Message, state: FSMContext):
        telegram_id = message.from_user.id
        args = message.get_args()
        referral_code = args if args else None
        add_user(telegram_id, referral_code)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
             InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
        ])
        await message.answer(get_text("select_language", "ru"), reply_markup=keyboard)
        await state.set_state(GameStates.AGE_CONFIRM)

    @dp.callback_query(lambda c: c.data.startswith("lang_"))
    async def set_language(callback: types.CallbackQuery, state: FSMContext):
        lang = callback.data.split("_")[1]
        conn = sqlite3.connect("betsmilebot.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET language = ? WHERE telegram_id = ?", (lang, callback.from_user.id))
        conn.commit()
        conn.close()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("confirm_18", lang), callback_data="confirm_18")]
        ])
        await callback.message.edit_text(get_text("age_confirm", lang), reply_markup=keyboard)

    @dp.callback_query(lambda c: c.data == "confirm_18")
    async def confirm_age(callback: types.CallbackQuery, state: FSMContext):
        lang = get_user(callback.from_user.id)[1]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("play", lang), callback_data="play")],
            [InlineKeyboardButton(text=get_text("profile", lang), callback_data="profile"),
             InlineKeyboardButton(text=get_text("deposit", lang), callback_data="deposit")],
            [InlineKeyboardButton(text=get_text("withdraw", lang), callback_data="withdraw"),
             InlineKeyboardButton(text=get_text("support", lang), callback_data="support")],
            [InlineKeyboardButton(text=get_text("terms", lang), url="https://your-terms-url.com")]
        ])
        await callback.message.edit_text(get_text("welcome", lang), reply_markup=keyboard)
        await state.clear()

    @dp.callback_query(lambda c: c.data == "play")
    async def play_menu(callback: types.CallbackQuery, state: FSMContext):
        lang = get_user(callback.from_user.id)[1]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("guess_number", lang), callback_data="game_guess_number"),
             InlineKeyboardButton(text=get_text("coin_flip", lang), callback_data="game_coin_flip")],
            [InlineKeyboardButton(text=get_text("find_card", lang), callback_data="game_find_card"),
             InlineKeyboardButton(text=get_text("dice", lang), callback_data="game_dice")],
            [InlineKeyboardButton(text=get_text("wheel", lang), callback_data="game_wheel"),
             InlineKeyboardButton(text=get_text("back", lang), callback_data="back")]
        ])
        await callback.message.edit_text(get_text("choose_game", lang), reply_markup=keyboard)
        await state.set_state(GameStates.SELECT_GAME)

    @dp.callback_query(lambda c: c.data.startswith("game_"))
    async def select_game(callback: types.CallbackQuery, state: FSMContext):
        lang = get_user(callback.from_user.id)[1]
        game_type = callback.data.split("_")[1]
        await state.update_data(game_type=game_type)
        await callback.message.edit_text(get_text("enter_amount", lang))
        await state.set_state(GameStates.ENTER_AMOUNT)

    @dp.message(GameStates.ENTER_AMOUNT)
    async def process_amount(message: types.Message, state: FSMContext):
        user = get_user(message.from_user.id)
        lang = user[1]
        try:
            amount = float(message.text)
            if amount < 0.5 or amount > 500:
                await message.answer(get_text("amount_range", lang))
                return
            if user[3] < amount and user[4] < amount:
                await message.answer(get_text("insufficient_balance", lang))
                return
            mode = "real" if user[4] >= amount else "demo"
            result, win_amount = play_game(user[0], mode, amount, (await state.get_data())["game_type"])
            if mode == "demo":
                update_balance(user[0], demo_balance=user[3] + win_amount - amount)
            else:
                update_balance(user[0], real_balance=user[4] + win_amount - amount)
                if win_amount > 0 and mode == "real":
                    conn = sqlite3.connect("betsmilebot.db")
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO transactions (telegram_id, amount, type, status) VALUES (?, ?, ?, ?)",
                                  (user[0], win_amount, "win", "completed"))
                    conn.commit()
                    conn.close()
            await message.answer_animation(animation=ANIMATION_GIFS[result], caption=get_text(result, lang))
            await asyncio.sleep(2)  # Задержка для анимации
        except ValueError:
            await message.answer(get_text("invalid_amount", lang))
        await state.clear()

    @dp.callback_query(lambda c: c.data == "deposit")
    async def deposit(callback: types.CallbackQuery):
        lang = get_user(callback.from_user.id)[1]
        payment_url = create_payment(callback.from_user.id, 0.5, "USD")
        if not payment_url:
            await callback.message.edit_text(get_text("payment_error", lang))
            return
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("pay", lang), url=payment_url)],
            [InlineKeyboardButton(text=get_text("back", lang), callback_data="back")]
        ])
        await callback.message.edit_text(get_text("deposit_info", lang), reply_markup=keyboard)

    @dp.callback_query(lambda c: c.data == "withdraw")
    async def withdraw(callback: types.CallbackQuery):
        user = get_user(callback.from_user.id)
        lang = user[1]
        if user[4] < 50:
            await callback.message.edit_text(get_text("min_withdraw", lang))
            return
        conn = sqlite3.connect("betsmilebot.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO transactions (telegram_id, amount, type, status) VALUES (?, ?, ?, ?)",
                      (user[0], user[4], "withdraw", "pending"))
        conn.commit()
        conn.close()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("back", lang), callback_data="back")]
        ])
        await callback.message.edit_text(get_text("withdraw_request", lang), reply_markup=keyboard)

    @dp.callback_query(lambda c: c.data == "profile")
    async def profile(callback: types.CallbackQuery):
        user = get_user(callback.from_user.id)
        lang = user[1]
        text = get_text("profile_info", lang).format(
            demo_balance=user[3], real_balance=user[4], referral_code=user[5]
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("back", lang), callback_data="back")]
        ])
        await callback.message.edit_text(text, reply_markup=keyboard)

    @dp.callback_query(lambda c: c.data == "support")
    async def support(callback: types.CallbackQuery):
        lang = get_user(callback.from_user.id)[1]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("back", lang), callback_data="back")]
        ])
        await callback.message.edit_text(get_text("support_info", lang), reply_markup=keyboard)

    @dp.callback_query(lambda c: c.data == "back")
    async def back(callback: types.CallbackQuery, state: FSMContext):
        lang = get_user(callback.from_user.id)[1]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("play", lang), callback_data="play")],
            [InlineKeyboardButton(text=get_text("profile", lang), callback_data="profile"),
             InlineKeyboardButton(text=get_text("deposit", lang), callback_data="deposit")],
            [InlineKeyboardButton(text=get_text("withdraw", lang), callback_data="withdraw"),
             InlineKeyboardButton(text=get_text("support", lang), callback_data="support")],
            [InlineKeyboardButton(text=get_text("terms", lang), url="https://your-terms-url.com")]
        ])
        await callback.message.edit_text(get_text("welcome", lang), reply_markup=keyboard)
        await state.clear()
