import requests
import time
from config import CRYPTOCLOUD_API_KEY, CRYPTOCLOUD_SHOP_ID
from database import update_balance, get_user
import logging

logger = logging.getLogger(__name__)

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
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            payment_url = response.json()["result"]["link"]
            logger.info(f"Payment created for user {telegram_id}: {payment_url}")
            return payment_url
        else:
            logger.error(f"Failed to create payment for user {telegram_id}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error creating payment for user {telegram_id}: {e}")
        return None
