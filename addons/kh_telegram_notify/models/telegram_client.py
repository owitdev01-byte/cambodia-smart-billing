import logging

import requests

_logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram_message(token, chat_id, text):
    if not token or not chat_id:
        _logger.warning("Telegram notification skipped: bot token or chat ID not configured.")
        return False
    try:
        response = requests.post(
            TELEGRAM_API_URL.format(token=token),
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        _logger.exception("Failed to send Telegram notification.")
        return False
