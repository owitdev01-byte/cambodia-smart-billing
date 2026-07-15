from odoo import models

from .telegram_client import send_telegram_message

STATUS_MESSAGES = {
    "pending": "\U0001F7E1 KHQR uploaded for invoice {name} ({amount} {currency}). Awaiting payment.",
    "paid": "\U00002705 Invoice {name} ({amount} {currency}) marked as paid via KHQR.",
}


class AccountMove(models.Model):
    _inherit = "account.move"

    def write(self, vals):
        tracked = "khqr_status" in vals
        previous_status = {move.id: move.khqr_status for move in self} if tracked else {}
        result = super().write(vals)
        if tracked:
            for move in self:
                if previous_status.get(move.id) != move.khqr_status and move.khqr_status in STATUS_MESSAGES:
                    move._notify_telegram_khqr_status()
        return result

    def _notify_telegram_khqr_status(self):
        self.ensure_one()
        company = self.company_id
        text = STATUS_MESSAGES[self.khqr_status].format(
            name=self.name,
            amount=self.amount_total,
            currency=self.currency_id.name,
        )
        send_telegram_message(company.telegram_bot_token, company.telegram_chat_id, text)
