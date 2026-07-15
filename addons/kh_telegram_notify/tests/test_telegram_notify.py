from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTelegramNotify(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Telegram Test Customer"})
        cls.usd = cls.env.ref("base.USD")
        cls.usd.active = True
        cls.env.company.write({
            "telegram_bot_token": "test-token",
            "telegram_chat_id": "12345",
        })

    def _create_posted_invoice(self):
        move = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.partner.id,
            "currency_id": self.usd.id,
            "invoice_date": fields.Date.context_today(self),
            "invoice_line_ids": [(0, 0, {
                "name": "Test line",
                "quantity": 1,
                "price_unit": 10.0,
            })],
        })
        move.action_post()
        return move

    @patch("odoo.addons.kh_telegram_notify.models.telegram_client.requests.post")
    def test_notifies_on_pending(self, mock_post):
        mock_post.return_value.raise_for_status.return_value = None
        move = self._create_posted_invoice()
        move.khqr_status = "pending"

        self.assertTrue(mock_post.called)
        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["chat_id"], "12345")
        self.assertIn(move.name, payload["text"])

    @patch("odoo.addons.kh_telegram_notify.models.telegram_client.requests.post")
    def test_no_notification_without_config(self, mock_post):
        self.env.company.write({"telegram_bot_token": False, "telegram_chat_id": False})
        move = self._create_posted_invoice()
        move.khqr_status = "pending"
        mock_post.assert_not_called()

    @patch("odoo.addons.kh_telegram_notify.models.telegram_client.requests.post")
    def test_no_duplicate_notification_when_status_unchanged(self, mock_post):
        mock_post.return_value.raise_for_status.return_value = None
        move = self._create_posted_invoice()
        move.khqr_status = "pending"
        mock_post.reset_mock()

        move.write({"khqr_status": "pending"})
        mock_post.assert_not_called()
