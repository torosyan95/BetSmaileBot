import requests
from config import CRYPTOCLOUD_API_KEY, CRYPTOCLOUD_SHOP_ID

def create_payment(telegram_id, amount, currency):
    url = "https://api.cryptocloud.plus/v1/invoice/create"
    headers = {
        "Authorization": f"Token {CRYPTOCLOUD_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "shop_id": CRYPTOCLOUD_SHOP_ID,
        "amount": amount,
        "currency": currency,
        "order_id": f"order_{telegram_id}_{int(time.time())}"
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["result"]["link"]
    return None
