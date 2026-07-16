import logging
import re

import requests

_logger = logging.getLogger(__name__)

NBC_EXCHANGE_RATE_URL = "https://www.nbc.gov.kh/english/economic_research/exchange_rate.php"
RATE_PATTERN = re.compile(
    r"Official Exchange Rate\s*:\s*<font[^>]*>\s*([\d.]+)\s*</font>\s*KHR\s*/\s*USD",
    re.IGNORECASE,
)
# NBC's server returns 403 for the default python-requests User-Agent.
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
}


def fetch_nbc_usd_khr_rate():
    """Fetch today's official KHR-per-USD rate from the National Bank of Cambodia.

    Returns a float (e.g. 4037.0), or None if the page can't be reached or parsed.
    NBC publishes one official rate per business day (~16:30 Cambodia time), not
    a live/real-time feed, so this is meant to be called at most a few times a day.
    """
    try:
        response = requests.get(NBC_EXCHANGE_RATE_URL, headers=REQUEST_HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        _logger.exception("Failed to reach the NBC exchange rate page.")
        return None

    match = RATE_PATTERN.search(response.text)
    if not match:
        _logger.error("Could not find the official exchange rate on the NBC page.")
        return None

    return float(match.group(1))
