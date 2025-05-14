#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Токен Telegram бота
TOKEN = "7941035327:AAFoTOoEC-t6AHPLp7GAs9H0S2BrmSzOrWc"

# ID администраторов бота
ADMIN_IDS = [
    int(os.environ.get("ADMIN_ID", "YOUR_TELEGRAM_ID"))  # Замените на ваш ID
]

# Данные для CryptoCloud API
CRYPTOCLOUD_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1dWlkIjoiTlRJNE16TT0iLCJ0eXBlIjoicHJvamVjdCIsInYiOiJhMWI4MDM0OTdlNjk3N2M2NDc1ZmRmYmZlNDk2MGRkY2NhMzc3MDEwYTY0MWMzMDNiMTU1Y2UwMGYxNmYzYzhkIiwiZXhwIjo4ODE0NzA5ODAzOH0.D16DZBUAU_iTVvLa-g4ISZAAKzezulvKjunWYRg4A6s"
CRYPTOCLOUD_SHOP_ID = "qSWZk4nBQJkwCkan"

# Настройки игры
DEFAULT_SETTINGS = {
    "demo_win_chance": 75,  # Шанс выигрыша в демо-режиме (%)
    "real_win_chance": 20,  # Шанс выигрыша в реальном режиме (%)
    "max_consecutive_wins": 2,  # Максимальное количество последовательных побед
    "warm_up_wins": 2,  # Количество гарантированных побед для новых пользователей
    "min_deposit": 0.5,  # Минимальная сумма пополнения ($)
    "min_withdraw": 50,  # Минимальная сумма вывода ($)
    "max_bet": 500,  # Максимальная ставка ($)
    "min_bet": 0.5,  # Минимальная ставка ($)
}

# Настройки игр
GAME_SETTINGS = {
    "guess_number": {
        "options": 5,  # Количество чисел для выбора
        "multiplier": 4  # Множитель выигрыша
    },
    "coin_flip": {
        "options": 2,  # Количество сторон монеты
        "multiplier": 1.9  # Множитель выигрыша
    },
    "find_card": {
        "options": 3,  # Количество карт
        "multiplier": 2.8  # Множитель выигрыша
    },
    "dice": {
        "win_values": [5, 6],  # Выигрышные значения на кубике
        "multipliers": {
            "5": 2,  # Множитель для 5
            "6": 3   # Множитель для 6
        }
    },
    "wheel": {
        "segments": [
            {"value": 0, "multiplier": 0},  # Проигрыш
            {"value": 1, "multiplier": 1.5},
            {"value": 0, "multiplier": 0},  # Проигрыш
            {"value": 2, "multiplier": 2},
            {"value": 0, "multiplier": 0},  # Проигрыш
            {"value": 1.2, "multiplier": 1.2},
            {"value": 0, "multiplier": 0},  # Проигрыш
            {"value": 3, "multiplier": 3},
            {"value": 0, "multiplier": 0},  # Проигрыш
            {"value": 1.8, "multiplier": 1.8}
        ]
    }
}
