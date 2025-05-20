import random
import sqlite3

def play_game(telegram_id, mode, amount, game_type):
    user = get_user(telegram_id)
    is_new_user = len(get_games(telegram_id)) < 3
    win_chance = 0.6 if is_new_user and mode == "real" else 0.75 if mode == "demo" else 0.25
    
    result = "lose"
    win_amount = 0
    
    if game_type == "guess_number":
        correct = random.randint(1, 5)
        user_guess = random.randint(1, 5)  # Симуляция выбора
        if random.random() < win_chance and user_guess == correct:
            result = "win_guess_number"
            win_amount = amount * 2
    elif game_type == "coin_flip":
        if random.random() < win_chance:
            result = "win_coin_flip"
            win_amount = amount * 2
    elif game_type == "find_card":
        if random.random() < win_chance:
            result = "win_find_card"
            win_amount = amount * 3
    elif game_type == "dice":
        if random.random() < win_chance:
            result = "win_dice"
            win_amount = amount * 2
    elif game_type == "wheel":
        if random.random() < win_chance:
            result = "win_wheel"
            win_amount = amount * 4
    
    conn = sqlite3.connect("betsmilebot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO games (telegram_id, game_type, amount, result) VALUES (?, ?, ?, ?)",
                  (telegram_id, game_type, amount, result))
    conn.commit()
    conn.close()
    
    return result, win_amount

def get_games(telegram_id):
    conn = sqlite3.connect("betsmilebot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM games WHERE telegram_id = ?", (telegram_id,))
    games = cursor.fetchall()
    conn.close()
    return games
