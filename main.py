#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import logging
import json
import os
import time
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

from config import TOKEN, ADMIN_IDS, CRYPTOCLOUD_API_KEY, CRYPTOCLOUD_SHOP_ID
from database import Database
from games import Games
from payment import Payment
from states import UserStates
from keyboards import Keyboards
from language import Language

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Инициализация компонентов
db = Database()
games = Games(db)
payment = Payment(db, CRYPTOCLOUD_API_KEY, CRYPTOCLOUD_SHOP_ID)
kb = Keyboards()
lang = Language()

# Обработчик команды /start
@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    
    # Проверка наличия пользователя в базе
    if not db.user_exists(user_id):
        # Если это новый пользователь, добавляем его в базу
        db.add_user(user_id, username)
        
        # Установка языка
        await message.answer("🇷🇺 Выберите язык / 🇬🇧 Choose language", 
                             reply_markup=kb.language_keyboard())
        
        await UserStates.language.set()
    else:
        # Если пользователь уже существует, показываем главное меню
        user_language = db.get_user_language(user_id)
        await show_main_menu(message, user_language)
        await state.finish()

# Выбор языка
@dp.callback_query_handler(lambda c: c.data in ['ru', 'en'], state=UserStates.language)
async def process_language(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    selected_language = callback_query.data
    
    # Сохраняем выбранный язык
    db.set_user_language(user_id, selected_language)
    
    # Приветственное сообщение и условия
    welcome_text = lang.get_message('welcome', selected_language)
    terms_text = lang.get_message('terms', selected_language)
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=welcome_text
    )
    
    # Добавляем демо-баланс
    db.update_demo_balance(user_id, 10.0)
    
    # Показываем условия использования
    terms_msg = await bot.send_message(
        callback_query.message.chat.id,
        terms_text,
        reply_markup=kb.terms_keyboard(selected_language)
    )
    
    await UserStates.terms.set()

# Принятие условий
@dp.callback_query_handler(lambda c: c.data == 'accept_terms', state=UserStates.terms)
async def accept_terms(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_language = db.get_user_language(user_id)
    
    # Отмечаем, что пользователь принял условия
    db.set_terms_accepted(user_id, True)
    
    # Удаляем сообщение с условиями
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    
    # Показываем главное меню
    await show_main_menu(callback_query.message, user_language)
    await state.finish()

# Показ главного меню
async def show_main_menu(message, language):
    menu_text = lang.get_message('main_menu', language)
    demo_balance = db.get_demo_balance(message.chat.id)
    real_balance = db.get_real_balance(message.chat.id)
    
    menu_text += f"\n\n{lang.get_message('demo_balance', language)}: ${demo_balance:.2f}"
    menu_text += f"\n{lang.get_message('real_balance', language)}: ${real_balance:.2f}"
    
    await message.answer(
        menu_text,
        reply_markup=kb.main_menu_keyboard(language)
    )

# Обработчик кнопки "Играть"
@dp.callback_query_handler(lambda c: c.data == 'play')
async def process_play(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_language = db.get_user_language(user_id)
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=lang.get_message('select_mode', user_language),
        reply_markup=kb.game_mode_keyboard(user_language)
    )

# Выбор режима игры
@dp.callback_query_handler(lambda c: c.data in ['demo_mode', 'real_mode'])
async def process_game_mode(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_language = db.get_user_language(user_id)
    game_mode = callback_query.data
    
    # Сохраняем выбранный режим
    await state.update_data(game_mode=game_mode)
    
    # Показываем список игр
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=lang.get_message('select_game', user_language),
        reply_markup=kb.games_keyboard(user_language)
    )
    
    await UserStates.game_selection.set()

# Выбор игры
@dp.callback_query_handler(lambda c: c.data in ['guess_number', 'coin_flip', 'find_card', 'dice', 'wheel'], state=UserStates.game_selection)
async def process_game_selection(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_language = db.get_user_language(user_id)
    game_choice = callback_query.data
    
    # Сохраняем выбранную игру
    await state.update_data(game_choice=game_choice)
    
    # Запрашиваем сумму ставки
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=lang.get_message('enter_bet', user_language),
        reply_markup=kb.bet_amounts_keyboard(user_language)
    )
    
    await UserStates.bet_amount.set()

# Выбор суммы ставки
@dp.callback_query_handler(lambda c: c.data.startswith('bet_'), state=UserStates.bet_amount)
async def process_bet_amount(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_language = db.get_user_language(user_id)
    bet_amount = float(callback_query.data.split('_')[1])
    
    # Получаем данные из состояния
    state_data = await state.get_data()
    game_mode = state_data.get('game_mode')
    game_choice = state_data.get('game_choice')
    
    # Проверяем достаточно ли средств
    sufficient_funds = False
    if game_mode == 'demo_mode':
        sufficient_funds = db.get_demo_balance(user_id) >= bet_amount
    else:  # real_mode
        sufficient_funds = db.get_real_balance(user_id) >= bet_amount
    
    if not sufficient_funds:
        insufficient_funds_text = lang.get_message('insufficient_funds', user_language)
        
        if game_mode == 'real_mode':
            # Предлагаем пополнить баланс
            await bot.edit_message_text(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                text=insufficient_funds_text,
                reply_markup=kb.deposit_keyboard(user_language)
            )
        else:
            # Возвращаем в главное меню
            await bot.edit_message_text(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                text=insufficient_funds_text,
                reply_markup=kb.back_to_menu_keyboard(user_language)
            )
        return
    
    # Сохраняем сумму ставки
    await state.update_data(bet_amount=bet_amount)
    
    # В зависимости от выбранной игры запускаем соответствующий процесс
    if game_choice == 'guess_number':
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=lang.get_message('choose_number', user_language),
            reply_markup=kb.guess_number_keyboard()
        )
        await UserStates.game_process.set()
    
    elif game_choice == 'coin_flip':
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=lang.get_message('choose_side', user_language),
            reply_markup=kb.coin_flip_keyboard(user_language)
        )
        await UserStates.game_process.set()
    
    elif game_choice == 'find_card':
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=lang.get_message('find_card_instruction', user_language),
            reply_markup=kb.find_card_keyboard()
        )
        await UserStates.game_process.set()
    
    elif game_choice == 'dice':
        # Отправляем анимацию кубика
        dice_msg = await bot.send_dice(callback_query.message.chat.id)
        dice_value = dice_msg.dice.value
        
        # Получаем результат игры
        state_data = await state.get_data()
        result = await games.play_dice(
            user_id, 
            dice_value, 
            bet_amount, 
            game_mode == 'demo_mode'
        )
        
        # Отправляем результат после небольшой задержки
        await asyncio.sleep(2)
        
        if result['win']:
            win_amount = bet_amount * result['multiplier']
            result_text = lang.get_message('you_win', user_language).format(amount=win_amount)
        else:
            result_text = lang.get_message('you_lose', user_language).format(amount=bet_amount)
        
        await bot.send_message(
            callback_query.message.chat.id,
            result_text,
            reply_markup=kb.after_game_keyboard(user_language)
        )
        
        # Обновляем баланс
        if game_mode == 'demo_mode':
            new_balance = db.get_demo_balance(user_id)
        else:
            new_balance = db.get_real_balance(user_id)
            
        balance_text = lang.get_message(
            'demo_balance' if game_mode == 'demo_mode' else 'real_balance', 
            user_language
        )
        await bot.send_message(
            callback_query.message.chat.id,
            f"{balance_text}: ${new_balance:.2f}"
        )
        
        await state.finish()
    
    elif game_choice == 'wheel':
        # Отправляем анимацию колеса удачи
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=lang.get_message('wheel_spinning', user_language)
        )
        
        # Имитируем вращение
        await asyncio.sleep(3)
        
        # Получаем результат игры
        state_data = await state.get_data()
        result = await games.play_wheel_of_fortune(
            user_id, 
            bet_amount, 
            game_mode == 'demo_mode'
        )
        
        # Отправляем результат
        if result['win']:
            win_amount = bet_amount * result['multiplier']
            result_text = lang.get_message('wheel_win', user_language).format(
                amount=win_amount, multiplier=result['multiplier']
            )
        else:
            result_text = lang.get_message('wheel_lose', user_language).format(amount=bet_amount)
        
        await bot.send_message(
            callback_query.message.chat.id,
            result_text,
            reply_markup=kb.after_game_keyboard(user_language)
        )
        
        # Обновляем баланс
        if game_mode == 'demo_mode':
            new_balance = db.get_demo_balance(user_id)
        else:
            new_balance = db.get_real_balance(user_id)
            
        balance_text = lang.get_message(
            'demo_balance' if game_mode == 'demo_mode' else 'real_balance', 
            user_language
        )
        await bot.send_message(
            callback_query.message.chat.id,
            f"{balance_text}: ${new_balance:.2f}"
        )
        
        await state.finish()

# Обработка выбора числа в игре "Угадай число"
@dp.callback_query_handler(lambda c: c.data.startswith('number_'), state=UserStates.game_process)
async def process_guess_number(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_language = db.get_user_language(user_id)
    chosen_number = int(callback_query.data.split('_')[1])
    
    # Получаем данные из состояния
    state_data = await state.get_data()
    game_mode = state_data.get('game_mode')
    bet_amount = state_data.get('bet_amount')
    
    # Отправляем сообщение об ожидании
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=lang.get_message('processing', user_language)
    )
    
    # Имитируем обработку
    await asyncio.sleep(2)
    
    # Получаем результат игры
    result = await games.play_guess_number(
        user_id, 
        chosen_number, 
        bet_amount, 
        game_mode == 'demo_mode'
    )
    
    # Отправляем результат
    if result['win']:
        result_text = lang.get_message('guess_win', user_language).format(
            number=result['winning_number'], amount=bet_amount*2
        )
    else:
        result_text = lang.get_message('guess_lose', user_language).format(
            chosen=chosen_number, winning=result['winning_number'], amount=bet_amount
        )
    
    await bot.send_message(
        callback_query.message.chat.id,
        result_text,
        reply_markup=kb.after_game_keyboard(user_language)
    )
    
    # Обновляем баланс
    if game_mode == 'demo_mode':
        new_balance = db.get_demo_balance(user_id)
    else:
        new_balance = db.get_real_balance(user_id)
        
    balance_text = lang.get_message(
        'demo_balance' if game_mode == 'demo_mode' else 'real_balance', 
        user_language
    )
    await bot.send_message(
        callback_query.message.chat.id,
        f"{balance_text}: ${new_balance:.2f}"
    )
    
    await state.finish()

# Обработка выбора стороны в игре "Орёл или Решка"
@dp.callback_query_handler(lambda c: c.data in ['heads', 'tails'], state=UserStates.game_process)
async def process_coin_flip(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_language = db.get_user_language(user_id)
    chosen_side = callback_query.data
    
    # Получаем данные из состояния
    state_data = await state.get_data()
    game_mode = state_data.get('game_mode')
    bet_amount = state_data.get('bet_amount')
    
    # Отправляем сообщение об ожидании
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=lang.get_message('flipping_coin', user_language)
    )
    
    # Имитируем подбрасывание монеты
    await asyncio.sleep(2)
    
    # Получаем результат игры
    result = await games.play_coin_flip(
        user_id, 
        chosen_side, 
        bet_amount, 
        game_mode == 'demo_mode'
    )
    
    # Отправляем результат
    if result['win']:
        result_text = lang.get_message('coin_win', user_language).format(
            side=lang.get_message(result['result'], user_language), 
            amount=bet_amount*2
        )
    else:
        result_text = lang.get_message('coin_lose', user_language).format(
            chosen=lang.get_message(chosen_side, user_language),
            result=lang.get_message(result['result'], user_language), 
            amount=bet_amount
        )
    
    await bot.send_message(
        callback_query.message.chat.id,
        result_text,
        reply_markup=kb.after_game_keyboard(user_language)
    )
    
    # Обновляем баланс
    if game_mode == 'demo_mode':
        new_balance = db.get_demo_balance(user_id)
    else:
        new_balance = db.get_real_balance(user_id)
        
    balance_text = lang.get_message(
        'demo_balance' if game_mode == 'demo_mode' else 'real_balance', 
        user_language
    )
    await bot.send_message(
        callback_query.message.chat.id,
        f"{balance_text}: ${new_balance:.2f}"
    )
    
    await state.finish()

# Обработка выбора карты в игре "Найди карту"
@dp.callback_query_handler(lambda c: c.data.startswith('card_'), state=UserStates.game_process)
async def process_find_card(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_language = db.get_user_language(user_id)
    chosen_card = int(callback_query.data.split('_')[1])
    
    # Получаем данные из состояния
    state_data = await state.get_data()
    game_mode = state_data.get('game_mode')
    bet_amount = state_data.get('bet_amount')
    
    # Отправляем сообщение об ожидании
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=lang.get_message('revealing_cards', user_language)
    )
    
    # Имитируем открытие карт
    await asyncio.sleep(2)
    
    # Получаем результат игры
    result = await games.play_find_card(
        user_id, 
        chosen_card, 
        bet_amount, 
        game_mode == 'demo_mode'
    )
    
    # Отправляем результат
    if result['win']:
        result_text = lang.get_message('card_win', user_language).format(
            card=result['winning_card'], amount=bet_amount*3
        )
    else:
        result_text = lang.get_message('card_lose', user_language).format(
            chosen=chosen_card, winning=result['winning_card'], amount=bet_amount
        )
    
    await bot.send_message(
        callback_query.message.chat.id,
        result_text,
        reply_markup=kb.after_game_keyboard(user_language)
    )
    
    # Обновляем баланс
    if game_mode == 'demo_mode':
        new_balance = db.get_demo_balance(user_id)
    else:
        new_balance = db.get_real_balance(user_id)
        
    balance_text = lang.get_message(
        'demo_balance' if game_mode == 'demo_mode' else 'real_balance', 
        user_language
    )
    await bot.send_message(
        callback_query.message.chat.id,
        f"{balance_text}: ${new_balance:.2f}"
    )
    
    await state.finish()

# Обработчик кнопки "Профиль"
@dp.callback_query_handler(lambda c: c.data == 'profile')
async def process_profile(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_language = db.get_user_language(user_id)
    
    # Получаем информацию о пользователе
    user_data = db.get_user_data(user_id)
    
    # Формируем текст профиля
    profile_text = lang.get_message('profile_title', user_language) + "\n\n"
    profile_text += f"ID: {user_id}\n"
    profile_text += f"{lang.get_message('demo_balance', user_language)}: ${user_data.get('demo_balance', 0):.2f}\n"
    profile_text += f"{lang.get_message('real_balance', user_language)}: ${user_data.get('real_balance', 0):.2f}\n"
    profile_text += f"{lang.get_message('games_played', user_language)}: {user_data.get('games_played', 0)}\n"
    profile_text += f"{lang.get_message('wins', user_language)}: {user_data.get('wins', 0)}\n"
    profile_text += f"{lang.get_message('losses', user_language)}: {user_data.get('losses', 0)}\n"
    profile_text += f"{lang.get_message('total_won', user_language)}: ${user_data.get('total_won', 0):.2f}\n"
    profile_text += f"{lang.get_message('total_lost', user_language)}: ${user_data.get('total_lost', 0):.2f}\n"
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=profile_text,
        reply_markup=kb.back_to_menu_keyboard(user_language)
    )

# Обработчик кнопки "Пополнить"
@dp.callback_query_handler(lambda c: c.data == 'deposit')
async def process_deposit(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_language = db.get_user_language(user_id)
    
    deposit_text = lang.get_message('deposit_instruction', user_language)
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=deposit_text,
        reply_markup=kb.deposit_amounts_keyboard(user_language)
    )

# Выбор суммы пополнения
@dp.callback_query_handler(lambda c: c.data.startswith('deposit_'))
async def process_deposit_amount(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_language = db.get_user_language(user_id)
    amount = float(callback_query.data.split('_')[1])
    
    # Создаем ссылку на оплату через CryptoCloud
    payment_url = await payment.create_invoice(user_id, amount)
    
    # Отправляем ссылку пользователю
    payment_text = lang.get_message('payment_link', user_language)
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=payment_text,
        reply_markup=kb.payment_keyboard(payment_url, user_language)
    )

# Обработчик кнопки "Вывод"
@dp.callback_query_handler(lambda c: c.data == 'withdraw')
async def process_withdraw(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_language = db.get_user_language(user_id)
    
    real_balance = db.get_real_balance(user_id)
    
    if real_balance < 50:
        insufficient_text = lang.get_message('insufficient_withdraw', user_language).format(min_amount=50)
        
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=insufficient_text,
            reply_markup=kb.back_to_menu_keyboard(user_language)
        )
        return
    
    withdraw_text = lang.get_message('withdraw_instruction', user_language).format(balance=real_balance)
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=withdraw_text,
        reply_markup=kb.withdraw_keyboard(user_language)
    )
    
    await UserStates.withdraw_amount.set()

# Ввод суммы для вывода
@dp.message_handler(state=UserStates.withdraw_amount)
async def process_withdraw_amount(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_language = db.get_user_language(user_id)
    
    try:
        amount = float(message.text)
        real_balance = db.get_real_balance(user_id)
        
        if amount < 50:
            await message.answer(
                lang.get_message('min_withdraw', user_language).format(min_amount=50),
                reply_markup=kb.back_to_menu_keyboard(user_language)
            )
            await state.finish()
            return
            
        if amount > real_balance:
            await message.answer(
                lang.get_message('insufficient_funds', user_language),
                reply_markup=kb.back_to_menu_keyboard(user_language)
            )
            await state.finish()
            return
        
        # Сохраняем сумму для вывода
        await state.update_data(withdraw_amount=amount)
        
        # Просим ввести реквизиты
        await message.answer(lang.get_message('enter_wallet', user_language))
        await UserStates.withdraw_wallet.set()
        
    except ValueError:
        await message.answer(
            lang.get_message('invalid_amount', user_language),
            reply_markup=kb.back_to_menu_keyboard(user_language)
        )
        await state.finish()

# Ввод кошелька для вывода
@dp.message_handler(state=UserStates.withdraw_wallet)
async def process_withdraw_wallet(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_language = db.get_user_language(user_id)
    wallet = message.text
    
    # Получаем сумму из состояния
    state_data = await state.get_data()
    amount = state_data.get('withdraw_amount')
    
    # Сохраняем запрос на вывод
    withdraw_id = db.add_withdraw_request(user_id, amount, wallet)
    
    # Уменьшаем баланс пользователя
    db.update_real_balance(user_id, -amount)
    
    # Отправляем уведомление админу
    for admin_id in ADMIN_IDS:
        await bot.send_message(
            admin_id,
            f"🔔 Новый запрос на вывод!\n\n"
            f"Пользователь: {user_id}\n"
            f"Сумма: ${amount:.2f}\n"
            f"Кошелек: {wallet}\n"
            f"ID запроса: {withdraw_id}",
            reply_markup=kb.admin_withdraw_keyboard(withdraw_id)
        )
    
    # Отправляем подтверждение пользователю
    await message.answer(
        lang.get_message('withdraw_success', user_language).format(amount=amount),
        reply_markup=kb.back_to_menu_keyboard(user_language)
    )
    
    await state.finish()

# Обработчик кнопки "Поддержка"
@dp.callback_query_handler(lambda c: c.data == 'support')
async def process_support(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_language = db.get_user_language(user_id)
    
    support_text = lang.get_message('support_instruction', user_language)
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=support_text,
        reply_markup=kb.back_to_menu_keyboard(user_language)
    )
    
    await UserStates.support.set()

# Обработка сообщения для поддержки
@dp.message_handler(state=UserStates.support)
async def process_support_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_language = db.get_user_language(user_id)
    support_message = message.text
    
    # Сохраняем сообщение в базе
    message_id = db.add_support_message(user_id, support_message)
    
    # Отправляем уведомление админу
    for admin_id in ADMIN_IDS:
        await bot.send_message(
            admin_id,
            f"🔔 Новое сообщение в поддержку!\n\n"
            f"Пользователь: {user_id}\n"
            f"Сообщение: {support_message}\n"
            f"ID сообщения: {message_id}",
            reply_markup=kb.admin_support_keyboard(user_id, message_id)
        )
    
    # Отправляем подтверждение пользователю
    await message.answer(
        lang.get_message('support_success', user_language),
        reply_markup=kb.back_to_menu_keyboard(user_language)
    )
    
    await state.finish()

# Обработчик кнопки "Назад в меню"
@dp.callback_query_handler(lambda c: c.data == 'back_to_menu', state='*')
async def back_to_menu(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_language = db.get_user_language(user_id)
    
    await state.finish()
    
    # Показываем главное меню
    menu_text = lang.get_message('main_menu', user_language)
    demo_balance = db.get_demo_balance(user_id)
    real_balance = db.get_real_balance(user_id)
    
    menu_text += f"\n\n{lang.get_message('demo_balance', user_language)}: ${demo_balance:.2f}"
    menu_text += f"\n{lang.get_message('real_balance', user_language)}: ${real_balance:.2f}"
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=menu_text,
        reply_markup=kb.main_menu_keyboard(user_language)
    )

# Обработчик кнопки "Играть снова"
@dp.callback_query_handler(lambda c: c.data == 'play_again')
async def play_again(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_language = db.get_user_language(user_id)
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=lang.get_message('select_mode', user_language),
        reply_markup=kb.game_mode_keyboard(user_language)
    )

# --- Административные обработчики ---

# Команда для доступа к админ-панели
@dp.message_handler(commands=['admin'])
async def cmd_admin(message: types.Message):
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS:
        return
    
    await message.answer(
        "🎮 Панель администратора BetSmileBot\n\n"
        "Выберите действие:",
        reply_markup=kb.admin_menu_keyboard()
    )

# Обработчик кнопок админ-панели
@dp.callback_query_handler(lambda c: c.data.startswith('admin_'))
async def process_admin_actions(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS:
        return
    
    action = callback_query.data.split('_')[1]
    
    if action == 'users':
        # Получаем список пользователей
        users = db.get_all_users()
        
        users_text = "👥 Список пользователей:\n\n"
        for user in users[:20]:  # Показываем только первых 20 пользователей
            users_text += f"ID: {user['id']}\n"
            users_text += f"Демо баланс: ${user['demo_balance']:.2f}\n"
            users_text += f"Реальный баланс: ${user['real_balance']:.2f}\n"
            users_text += f"Игр сыграно: {user['games_played']}\n"
            users_text += "---------\n"
        
        users_text += f"\nВсего пользователей: {len(users)}"
        
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=users_text,
            reply_markup=kb.admin_back_keyboard()
        )
    
    elif action == 'stats':
        # Получаем статистику игр
        stats = db.get_game_stats()
        
        stats_text = "📊 Статистика игр:\n\n"
        stats_text += f"Всего игр: {stats['total_games']}\n"
        stats_text += f"Выигрышей: {stats['total_wins']} ({stats['win_percentage']:.2f}%)\n"
        stats_text += f"Проигрышей: {stats['total_losses']} ({stats['loss_percentage']:.2f}%)\n\n"
        
        stats_text += "По играм:\n"
        for game, count in stats['games'].items():
            stats_text += f"- {game}: {count} игр\n"
        
        stats_text += f"\nОбщая прибыль: ${stats['total_profit']:.2f}"
        
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=stats_text,
            reply_markup=kb.admin_back_keyboard()
        )
    
    elif action == 'withdrawals':
        # Получаем список запросов на вывод
        withdrawals = db.get_pending_withdrawals()
        
        withdraw_text = "💸 Запросы на вывод:\n\n"
        
        if not withdrawals:
            withdraw_text += "Нет активных запросов на вывод."
        else:
            for withdraw in withdrawals:
                withdraw_text += f"ID запроса: {withdraw['id']}\n"
                withdraw_text += f"Пользователь: {withdraw['user_id']}\n"
                withdraw_text += f"Сумма: ${withdraw['amount']:.2f}\n"
                withdraw_text += f"Кошелек: {withdraw['wallet']}\n"
                withdraw_text += f"Статус: {withdraw['status']}\n"
                withdraw_text += f"Дата: {withdraw['date']}\n"
                withdraw_text += "---------\n"
        
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=withdraw_text,
            reply_markup=kb.admin_back_keyboard()
        )
    
    elif action == 'add_balance':
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="Введите ID пользователя для пополнения баланса:",
            reply_markup=kb.admin_back_keyboard()
        )
        await UserStates.admin_add_balance_user.set()
    
    elif action == 'settings':
        settings = db.get_settings()
        
        settings_text = "⚙️ Настройки бота:\n\n"
        settings_text += f"Демо шанс выигрыша: {settings['demo_win_chance']}%\n"
        settings_text += f"Реальный шанс выигрыша: {settings['real_win_chance']}%\n"
        settings_text += f"Макс. последовательных побед: {settings['max_consecutive_wins']}\n"
        settings_text += f"Подогрев для новых: {settings['warm_up_wins']} побед\n"
        
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=settings_text,
            reply_markup=kb.admin_settings_keyboard()
        )
    
    elif action == 'back':
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="🎮 Панель администратора BetSmileBot\n\nВыберите действие:",
            reply_markup=kb.admin_menu_keyboard()
        )

# Ввод ID пользователя для пополнения
@dp.message_handler(state=UserStates.admin_add_balance_user)
async def admin_add_balance_user(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        
        # Проверяем, существует ли пользователь
        if not db.user_exists(user_id):
            await message.answer(
                "Пользователь не найден. Попробуйте еще раз:",
                reply_markup=kb.admin_cancel_keyboard()
            )
            return
        
        # Сохраняем ID пользователя
        await state.update_data(target_user_id=user_id)
        
        # Запрашиваем сумму
        await message.answer(
            f"Введите сумму для пополнения баланса пользователя {user_id}:",
            reply_markup=kb.admin_cancel_keyboard()
        )
        
        await UserStates.admin_add_balance_amount.set()
        
    except ValueError:
        await message.answer(
            "Некорректный ID пользователя. Попробуйте еще раз:",
            reply_markup=kb.admin_cancel_keyboard()
        )

# Ввод суммы для пополнения
@dp.message_handler(state=UserStates.admin_add_balance_amount)
async def admin_add_balance_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        
        # Получаем ID пользователя из состояния
        state_data = await state.get_data()
        user_id = state_data.get('target_user_id')
        
        # Пополняем баланс
        db.update_real_balance(user_id, amount)
        
        # Отправляем уведомление пользователю
        user_language = db.get_user_language(user_id)
        await bot.send_message(
            user_id,
            lang.get_message('admin_added_balance', user_language).format(amount=amount)
        )
        
        # Отправляем подтверждение админу
        await message.answer(
            f"✅ Баланс пользователя {user_id} успешно пополнен на ${amount:.2f}",
            reply_markup=kb.admin_back_inline_keyboard()
        )
        
        await state.finish()
        
    except ValueError:
        await message.answer(
            "Некорректная сумма. Попробуйте еще раз:",
            reply_markup=kb.admin_cancel_keyboard()
        )

# Подтверждение или отклонение запроса на вывод
@dp.callback_query_handler(lambda c: c.data.startswith('withdraw_'))
async def process_withdraw_decision(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS:
        return
    
    action, withdraw_id = callback_query.data.split('_')[1:3]
    withdraw_id = int(withdraw_id)
    
    # Получаем данные запроса
    withdraw_data = db.get_withdraw_request(withdraw_id)
    
    if not withdraw_data:
        await bot.answer_callback_query(callback_query.id, "Запрос не найден")
        return
    
    if withdraw_data['status'] != 'pending':
        await bot.answer_callback_query(callback_query.id, "Запрос уже обработан")
        return
    
    target_user_id = withdraw_data['user_id']
    amount = withdraw_data['amount']
    user_language = db.get_user_language(target_user_id)
    
    if action == 'approve':
        # Подтверждаем запрос на вывод
        db.update_withdraw_status(withdraw_id, 'approved')
        
        # Отправляем уведомление пользователю
        await bot.send_message(
            target_user_id,
            lang.get_message('withdraw_approved', user_language).format(amount=amount)
        )
        
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=f"✅ Запрос на вывод #{withdraw_id} на сумму ${amount:.2f} подтвержден!"
        )
    
    elif action == 'reject':
        # Отклоняем запрос на вывод
        db.update_withdraw_status(withdraw_id, 'rejected')
        
        # Возвращаем средства пользователю
        db.update_real_balance(target_user_id, amount)
        
        # Отправляем уведомление пользователю
        await bot.send_message(
            target_user_id,
            lang.get_message('withdraw_rejected', user_language).format(amount=amount)
        )
        
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=f"❌ Запрос на вывод #{withdraw_id} на сумму ${amount:.2f} отклонен. Средства возвращены пользователю."
        )

# Ответ на сообщение поддержки
@dp.callback_query_handler(lambda c: c.data.startswith('support_reply_'))
async def process_support_reply(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in ADMIN_IDS:
        return
    
    target_user_id = int(callback_query.data.split('_')[2])
    message_id = int(callback_query.data.split('_')[3])
    
    # Сохраняем ID пользователя и сообщения
    await state.update_data(target_user_id=target_user_id, message_id=message_id)
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=f"Введите ответ для пользователя {target_user_id}:",
        reply_markup=kb.admin_cancel_keyboard()
    )
    
    await UserStates.admin_support_reply.set()

# Ввод ответа на сообщение поддержки
@dp.message_handler(state=UserStates.admin_support_reply)
async def admin_support_reply(message: types.Message, state: FSMContext):
    admin_id = message.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if admin_id not in ADMIN_IDS:
        await state.finish()
        return
    
    reply_text = message.text
    
    # Получаем данные из состояния
    state_data = await state.get_data()
    target_user_id = state_data.get('target_user_id')
    message_id = state_data.get('message_id')
    
    # Обновляем статус сообщения
    db.update_support_message_status(message_id, 'answered')
    
    # Сохраняем ответ
    db.add_support_reply(message_id, admin_id, reply_text)
    
    # Отправляем ответ пользователю
    user_language = db.get_user_language(target_user_id)
    await bot.send_message(
        target_user_id,
        lang.get_message('support_reply', user_language).format(message=reply_text)
    )
    
    # Отправляем подтверждение админу
    await message.answer(
        f"✅ Ответ пользователю {target_user_id} успешно отправлен!",
        reply_markup=kb.admin_back_inline_keyboard()
    )
    
    await state.finish()

# Проверка платежей
async def check_payments_callback():
    # Получаем все неоплаченные счета
    invoices = db.get_pending_invoices()
    
    for invoice in invoices:
        invoice_id = invoice['invoice_id']
        user_id = invoice['user_id']
        amount = invoice['amount']
        
        # Проверяем статус счета
        status = await payment.check_invoice(invoice_id)
        
        if status == 'paid':
            # Обновляем статус счета
            db.update_invoice_status(invoice_id, 'paid')
            
            # Пополняем баланс пользователя
            db.update_real_balance(user_id, amount)
            
            # Отправляем уведомление пользователю
            user_language = db.get_user_language(user_id)
            await bot.send_message(
                user_id,
                lang.get_message('payment_success', user_language).format(amount=amount)
            )

# Запуск проверки платежей каждые 5 минут
async def scheduled_tasks():
    while True:
        await check_payments_callback()
        await asyncio.sleep(300)  # 5 минут

# Обработка всех остальных сообщений (удаляем)
@dp.message_handler()
async def delete_message(message: types.Message):
    await message.delete()

# Запуск бота
async def on_startup(dp):
    # Запускаем фоновые задачи
    asyncio.create_task(scheduled_tasks())
    
    # Устанавливаем команды бота
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Запустить бота")
    ])
    
    # Уведомляем админов о запуске
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "🎮 Бот BetSmileBot запущен!")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение админу {admin_id}: {e}")
    
    logger.info("Бот запущен!")

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
