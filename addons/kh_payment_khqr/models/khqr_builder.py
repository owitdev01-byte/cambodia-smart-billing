import hashlib

CURRENCY_ISO_NUMERIC = {
    "USD": "840",
    "KHR": "116",
}


def _tlv(tag, value):
    value = str(value)
    return f"{tag}{len(value):02d}{value}"


def _crc16_ccitt(payload):
    crc = 0xFFFF
    for byte in payload.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return format(crc, "04X")


def build_khqr_payload(bakong_account_id, merchant_name, merchant_city, amount, currency, bill_number, merchant_category_code="5999"):
    """Build a dynamic (amount-specified) KHQR/EMVCo payload string.

    Tag layout follows NBC's published Bakong KHQR spec as of this writing;
    verify against Bakong's sandbox before relying on this for real transactions.
    """
    if currency not in CURRENCY_ISO_NUMERIC:
        raise ValueError(f"Unsupported KHQR currency: {currency}")

    merchant_account_info = _tlv("00", "KHQR") + _tlv("01", bakong_account_id)

    payload = "".join([
        _tlv("00", "01"),                            # Payload Format Indicator
        _tlv("01", "12"),                             # Point of Initiation: dynamic (one-time)
        _tlv("29", merchant_account_info),            # Merchant Account Info (KHQR)
        _tlv("52", merchant_category_code),           # Merchant Category Code
        _tlv("53", CURRENCY_ISO_NUMERIC[currency]),   # Transaction Currency (ISO 4217 numeric)
        _tlv("54", f"{amount:.2f}"),                  # Transaction Amount
        _tlv("58", "KH"),                             # Country Code
        _tlv("59", merchant_name[:25]),                # Merchant Name
        _tlv("60", merchant_city[:15]),                # Merchant City
        _tlv("62", _tlv("01", bill_number[:25])),      # Additional Data: Bill Number
    ])

    payload_with_crc_tag = payload + "6304"
    return payload_with_crc_tag + _crc16_ccitt(payload_with_crc_tag)


def khqr_md5(qr_string):
    """Bakong's check_transaction_by_md5 API keys transactions off this hash."""
    return hashlib.md5(qr_string.encode("utf-8")).hexdigest()
