#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import time
import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных и создание необходимых таблиц"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Создаем таблицу пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            demo_balance REAL DEFAULT 10.0,
            real_balance REAL DEFAULT 0.0,
            language TEXT DEFAULT 'ru',
            registered_at TEXT,
            last_active TEXT,
            terms_accepted INTEGER DEFAULT 0,
            games_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            total_won REAL DEFAULT 0.0,
            total_lost REAL DEFAULT 0.0,
            consecutive_wins INTEGER DEFAULT 0,
            warm_up_wins INTEGER DEFAULT 2
        )
        ''')
        
        # Создаем таблицу игр
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game_type TEXT,
            bet_amount REAL,
            result TEXT,
            win_amount REAL DEFAULT 0.0,
            is_demo INTEGER DEFAULT 0,
            played_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Создаем таблицу платежей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            invoice_id TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Создаем таблицу запросов на вывод
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            wallet TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Создаем таблицу сообщений поддержки
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS support_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Создаем таблицу ответов на сообщения поддержки
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS support_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            admin_id INTEGER,
            reply TEXT,
            created_at TEXT,
            FOREIGN KEY (message_id) REFERENCES support_messages (id)
        )
        ''')
        
        # Создаем таблицу настроек
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            value TEXT
        )
        ''')
        
        from config import DEFAULT_SETTINGS
        
        # Добавляем настройки по умолчанию, если их нет
        for key, value in DEFAULT_SETTINGS.items():
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, str(value))
            )
        
        conn.commit()
        conn.close()
    
    def user_exists(self, user_id):
        """Проверка существования пользователя в базе"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result is not None
    
    def add_user(self, user_id, username):
        """Добавление нового пользователя в базу"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            """
            INSERT INTO users 
            (id, username, registered_at, last_active) 
            VALUES (?, ?, ?, ?)
            """,
            (user_id, username, now, now)
        )
        
        conn.commit()
        conn.close()
    
    def get_user_language(self, user_id):
        """Получение языка пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT language FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result else 'ru'
    
    def set_user_language(self, user_id, language):
        """Установка языка пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET language = ? WHERE id = ?",
            (language, user_id)
        )
        
        conn.commit()
        conn.close()
    
    def get_demo_balance(self, user_id):
        """Получение демо-баланса пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT demo_balance FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result else 0.0
    
    def get_real_balance(self, user_id):
        """Получение реального баланса пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT real_balance FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result else 0.0
    
    def update_demo_balance(self, user_id, amount):
        """Обновление демо-баланса пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Получаем текущий баланс
        cursor.execute("SELECT demo_balance FROM users WHERE id = ?", (user_id,))
        current_balance = cursor.fetchone()[0]
        
        # Обновляем баланс
        new_balance = current_balance + amount
        
        # Предотвращаем отрицательный баланс
        if new_balance < 0:
            new_balance = 0
        
        cursor.execute(
            "UPDATE users SET demo_balance = ? WHERE id = ?",
            (new_balance, user_id)
        )
        
        conn.commit()
        conn.close()
        
        return new_balance
    
    def update_real_balance(self, user_id, amount):
        """Обновление реального баланса пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Получаем текущий баланс
        cursor.execute("SELECT real_balance FROM users WHERE id = ?", (user_id,))
        current_balance = cursor.fetchone()[0]
        
        # Обновляем баланс
        new_balance = current_balance + amount
        
        # Предотвращаем отрицательный баланс
        if new_balance < 0:
            new_balance = 0
        
        cursor.execute(
            "UPDATE users SET real_balance = ? WHERE id = ?",
            (new_balance, user_id)
        )
        
        conn.commit()
        conn.close()
        
        return new_balance
    
    def set_terms_accepted(self, user_id, accepted):
        """Установка статуса принятия условий"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET terms_accepted = ? WHERE id = ?",
            (1 if accepted else 0, user_id)
        )
        
        conn.commit()
        conn.close()
    
    def get_user_data(self, user_id):
        """Получение всех данных пользователя"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return dict(result)
        return {}
    
    def record_game(self, user_id, game_type, bet_amount, result, win_amount, is_demo):
        """Запись результата игры"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            """
            INSERT INTO games 
            (user_id, game_type, bet_amount, result, win_amount, is_demo, played_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, game_type, bet_amount, result, win_amount, 1 if is_demo else 0, now)
        )
        
        # Обновляем статистику пользователя
        cursor.execute(
            "UPDATE users SET games_played = games_played + 1 WHERE id = ?",
            (user_id,)
        )
        
        if result == 'win':
            cursor.execute(
                "UPDATE users SET wins = wins + 1, total_won = total_won + ? WHERE id = ?",
                (win_amount, user_id)
            )
            
            # Увеличиваем счетчик последовательных побед
            cursor.execute(
                "UPDATE users SET consecutive_wins = consecutive_wins + 1 WHERE id = ?",
                (user_id,)
            )
        else:
            cursor.execute(
                "UPDATE users SET losses = losses + 1, total_lost = total_lost + ? WHERE id = ?",
                (bet_amount, user_id)
            )
            
            # Сбрасываем счетчик последовательных побед
            cursor.execute(
                "UPDATE users SET consecutive_wins = 0 WHERE id = ?",
                (user_id,)
            )
        
        conn.commit()
        conn.close()
    
    def get_consecutive_wins(self, user_id):
        """Получение количества последовательных побед"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT consecutive_wins FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result else 0
    
    def get_warm_up_wins(self, user_id):
        """Получение оставшихся гарантированных побед для нового пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT warm_up_wins FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result else 0
    
    def reduce_warm_up_wins(self, user_id):
        """Уменьшение счетчика гарантированных побед"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET warm_up_wins = warm_up_wins - 1 WHERE id = ? AND warm_up_wins > 0",
            (user_id,)
        )
        
        conn.commit()
        conn.close()
    
    def add_payment_invoice(self, user_id, amount, invoice_id):
        """Добавление счета на оплату"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            """
            INSERT INTO payments 
            (user_id, amount, invoice_id, created_at, updated_at) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, amount, invoice_id, now, now)
        )
        
        conn.commit()
        conn.close()
    
    def update_invoice_status(self, invoice_id, status):
        """Обновление статуса счета"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            "UPDATE payments SET status = ?, updated_at = ? WHERE invoice_id = ?",
            (status, now, invoice_id)
        )
        
        conn.commit()
        conn.close()
    
    def get_pending_invoices(self):
        """Получение неоплаченных счетов"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM payments WHERE status = 'pending'"
        )
        result = cursor.fetchall()
        
        conn.close()
        
        return [dict(row) for row in result]
    
    def add_withdraw_request(self, user_id, amount, wallet):
        """Добавление запроса на вывод"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            """
            INSERT INTO withdrawals 
            (user_id, amount, wallet, created_at, updated_at) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, amount, wallet, now, now)
        )
        
        # Получаем ID созданного запроса
        withdraw_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return withdraw_id
    
    def update_withdraw_status(self, withdraw_id, status):
        """Обновление статуса запроса на вывод"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            "UPDATE withdrawals SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, withdraw_id)
        )
        
        conn.commit()
        conn.close()
    
    def get_withdraw_request(self, withdraw_id):
        """Получение данных запроса на вывод"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM withdrawals WHERE id = ?",
            (withdraw_id,)
        )
        result = cursor.fetchone()
        
        conn.close()
        
        return dict(result) if result else None
    
    def get_pending_withdrawals(self):
        """Получение ожидающих запросов на вывод"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM withdrawals WHERE status = 'pending' ORDER BY created_at DESC"
        )
        result = cursor.fetchall()
        
        conn.close()
        
        return [dict(row) for row in result]
    
    def add_support_message(self, user_id, message):
        """Добавление сообщения в поддержку"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            """
            INSERT INTO support_messages 
            (user_id, message, created_at) 
            VALUES (?, ?, ?)
            """,
            (user_id, message, now)
        )
        
        # Получаем ID созданного сообщения
        message_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return message_id
    
    def update_support_message_status(self, message_id, status):
        """Обновление статуса сообщения в поддержку"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE support_messages SET status = ? WHERE id = ?",
            (status, message_id)
        )
        
        conn.commit()
        conn.close()
    
    def add_support_reply(self, message_id, admin_id, reply):
        """Добавление ответа на сообщение в поддержку"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            """
            INSERT INTO support_replies 
            (message_id, admin_id, reply, created_at) 
            VALUES (?, ?, ?, ?)
            """,
            (message_id, admin_id, reply, now)
        )
        
        conn.commit()
        conn.close()
    
    def get_all_users(self):
        """Получение списка всех пользователей"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users ORDER BY registered_at DESC")
        result = cursor.fetchall()
        
        conn.close()
        
        return [dict(row) for row in result]
    
    def get_game_stats(self):
        """Получение статистики игр"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Общая статистика
        cursor.execute("SELECT COUNT(*) FROM games")
        total_games = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM games WHERE result = 'win'")
        total_wins = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM games WHERE result = 'lose'")
        total_losses = cursor.fetchone()[0]
        
        # Статистика по играм
        cursor.execute("SELECT game_type, COUNT(*) FROM games GROUP BY game_type")
        games_by_type = cursor.fetchall()
        
        # Общая прибыль
        cursor.execute("SELECT SUM(bet_amount) FROM games WHERE result = 'lose' AND is_demo = 0")
        money_won = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(win_amount) FROM games WHERE result = 'win' AND is_demo = 0")
        money_lost = cursor.fetchone()[0] or 0
        
        total_profit = money_won - money_lost
        
        conn.close()
        
        # Формируем статистику
        win_percentage = (total_wins / total_games * 100) if total_games > 0 else 0
        loss_percentage = (total_losses / total_games * 100) if total_games > 0 else 0
        
        games_dict = {game_type: count for game_type, count in games_by_type}
        
        return {
            "total_games": total_games,
            "total_wins": total_wins,
            "total_losses": total_losses,
            "win_percentage": win_percentage,
            "loss_percentage": loss_percentage,
            "games": games_dict,
            "total_profit": total_profit
        }
    
    def get_settings(self):
        """Получение настроек"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT key, value FROM settings")
        settings = cursor.fetchall()
        
        conn.close()
        
        # Преобразуем в словарь
        settings_dict = {}
        for key, value in settings:
            try:
                # Пытаемся преобразовать значение в число
                settings_dict[key] = float(value) if '.' in value else int(value)
            except ValueError:
                settings_dict[key] = value
        
        return settings_dict
    
    def update_setting(self, key, value):
        """Обновление настройки"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE settings SET value = ? WHERE key = ?",
            (str(value), key)
        )
        
        conn.commit()
        conn.close()
    
    def get_setting(self, key):
        """Получение значения настройки"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            value = result[0]
            # Пытаемся преобразовать в число
            try:
                return float(value) if '.' in value else int(value)
            except ValueError:
                return value
        
        from config import DEFAULT_SETTINGS
        return DEFAULT_SETTINGS.get(key)
