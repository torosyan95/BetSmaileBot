# Ссылки на GIF-анимации для каждой игры (победа и проигрыш)
ANIMATION_GIFS = {
    "win_guess_number": "https://media1.tenor.com/m/9q4XU0p7YhUAAAAC/win-winner.gif",  # Анимация победы (угадал число)
    "win_coin_flip": "https://media1.tenor.com/m/3aI1hXgT5p0AAAAC/coin-flip-win.gif",  # Анимация победы (орёл/решка)
    "win_find_card": "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",  # Анимация победы (найди карту)
    "win_dice": "https://media1.tenor.com/m/4oN0Zq1f5eUAAAAC/dice-roll-win.gif",  # Анимация победы (кубик)
    "win_wheel": "https://media.giphy.com/media/26ufnwz3w8V3zV9gI/giphy.gif",  # Анимация победы (колесо удачи)
    "lose": "https://media1.tenor.com/m/J6zJ1Xq5f5IAAAAC/sad-lose.gif"  # Анимация проигрыша
}

# Тексты на русском и английском языках
TEXTS = {
    "ru": {
        "select_language": "🌍 Выберите язык:",
        "age_confirm": "Для продолжения подтвердите, что вам 18+ и вы согласны с условиями использования.",
        "confirm_18": "✅ Подтверждаю 18+",
        "welcome": "Добро пожаловать в @BetSmileBot! 🎉\nЭто развлекательный бот с мини-играми.\nНачните играть и получайте удовольствие!",
        "play": "🎮 Играть",
        "profile": "👤 Профиль",
        "deposit": "💰 Пополнить",
        "withdraw": "📤 Вывод",
        "support": "💬 Поддержка",
        "terms": "📜 Условия",
        "choose_game": "🎲 Выберите игру:",
        "guess_number": "🔢 Угадай число",
        "coin_flip": "🪙 Орёл или решка",
        "find_card": "🃏 Найди карту",
        "dice": "🎲 Кубик",
        "wheel": "🎡 Колесо удачи",
        "back": "🔙 Назад",
        "enter_amount": "💸 Введите сумму (0.5–500$):",
        "amount_range": "❌ Сумма должна быть от 0.5 до 500$!",
        "insufficient_balance": "⚠️ Недостаточно средств на балансе!",
        "invalid_amount": "❌ Некорректная сумма! Введите число.",
        "win_guess_number": "🎉 Победа! Вы угадали число! 🏆",
        "win_coin_flip": "🎉 Победа! Орёл/решка угаданы! 🪙",
        "win_find_card": "🎉 Победа! Карта найдена! 🃏",
        "win_dice": "🎉 Победа! Кубик принёс удачу! 🎲",
        "win_wheel": "🎉 Победа! Колесо удачи за вас! 🎡",
        "lose": "😔 Увы, не повезло! Попробуйте снова! 🍀",
        "deposit_info": "💳 Пополните баланс через CryptoCloud:",
        "pay": "💵 Оплатить",
        "payment_error": "⚠️ Ошибка при создании платежа! Попробуйте позже.",
        "withdraw_request": "✅ Заявка на вывод создана. Ожидайте подтверждения от админа.",
        "min_withdraw": "⚠️ Минимальная сумма для вывода — $50!",
        "profile_info": "👤 Профиль\n💎 Демо-баланс: ${demo_balance}\n💰 Реальный баланс: ${real_balance}\n🔗 Реферальный код: {referral_code}",
        "support_info": "📧 Свяжитесь с поддержкой: @BetSmileSupport"
    },
    "en": {
        "select_language": "🌍 Select language:",
        "age_confirm": "Please confirm that you are 18+ and agree with the terms of use.",
        "confirm_18": "✅ Confirm 18+",
        "welcome": "Welcome to @BetSmileBot! 🎉\nThis is an entertainment bot with mini-games.\nStart playing and have fun!",
        "play": "🎮 Play",
        "profile": "👤 Profile",
        "deposit": "💰 Deposit",
        "withdraw": "📤 Withdraw",
        "support": "💬 Support",
        "terms": "📜 Terms",
        "choose_game": "🎲 Choose a game:",
        "guess_number": "🔢 Guess Number",
        "coin_flip": "🪙 Coin Flip",
        "find_card": "🃏 Find Card",
        "dice": "🎲 Dice",
        "wheel": "🎡 Wheel of Fortune",
        "back": "🔙 Back",
        "enter_amount": "💸 Enter amount ($0.5–$500):",
        "amount_range": "❌ Amount must be between $0.5 and $500!",
        "insufficient_balance": "⚠️ Insufficient balance!",
        "invalid_amount": "❌ Invalid amount! Enter a number.",
        "win_guess_number": "🎉 Win! You guessed the number! 🏆",
        "win_coin_flip": "🎉 Win! Coin flip guessed correctly! 🪙",
        "win_find_card": "🎉 Win! Card found! 🃏",
        "win_dice": "🎉 Win! Dice brought luck! 🎲",
        "win_wheel": "🎉 Win! Wheel of fortune is on your side! 🎡",
        "lose": "😔 No luck this time! Try again! 🍀",
        "deposit_info": "💳 Deposit via CryptoCloud:",
        "pay": "💵 Pay",
        "payment_error": "⚠️ Error creating payment! Try again later.",
        "withdraw_request": "✅ Withdrawal request created. Await admin confirmation.",
        "min_withdraw": "⚠️ Minimum withdrawal amount is $50!",
        "profile_info": "👤 Profile\n💎 Demo Balance: ${demo_balance}\n💰 Real Balance: ${real_balance}\n🔗 Referral Code: {referral_code}",
        "support_info": "📧 Contact support: @BetSmileSupport"
    }
}

def get_text(key, lang):
    """
    Получить текст на указанном языке.
    Если язык или ключ не найдены, возвращается текст на русском.
    """
    return TEXTS.get(lang, TEXTS["ru"]).get(key, "Text not found")
