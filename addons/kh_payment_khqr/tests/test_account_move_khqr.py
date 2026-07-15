import base64

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged

FAKE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


@tagged("post_install", "-at_install")
class TestAccountMoveKhqr(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "KHQR Test Customer"})
        cls.usd = cls.env.ref("base.USD")
        cls.usd.active = True

    def _create_invoice(self, move_type="out_invoice", currency=None, post=True):
        move = self.env["account.move"].create({
            "move_type": move_type,
            "partner_id": self.partner.id,
            "currency_id": (currency or self.usd).id,
            "invoice_date": fields.Date.context_today(self),
            "invoice_line_ids": [(0, 0, {
                "name": "Test line",
                "quantity": 1,
                "price_unit": 10.0,
            })],
        })
        if post:
            move.action_post()
        return move

    def _upload(self, move):
        move.write({"khqr_qr_image": base64.b64encode(FAKE_PNG)})

    def test_upload_on_draft_invoice_blocked(self):
        move = self._create_invoice(post=False)
        with self.assertRaises(ValidationError):
            self._upload(move)

    def test_upload_on_vendor_bill_blocked(self):
        move = self._create_invoice(move_type="in_invoice", post=True)
        with self.assertRaises(ValidationError):
            self._upload(move)

    def test_upload_on_unsupported_currency_blocked(self):
        eur = self.env.ref("base.EUR")
        eur.active = True
        move = self._create_invoice(currency=eur, post=True)
        with self.assertRaises(ValidationError):
            self._upload(move)

    def test_upload_on_posted_usd_invoice_sets_pending(self):
        move = self._create_invoice(post=True)
        self._upload(move)
        self.assertTrue(move.khqr_qr_image)

    def test_mark_as_paid_without_upload_blocked(self):
        move = self._create_invoice(post=True)
        with self.assertRaises(UserError):
            move.action_confirm_khqr_payment()

    def test_mark_as_paid_registers_payment(self):
        move = self._create_invoice(post=True)
        self._upload(move)
        move.khqr_status = "pending"
        move.action_confirm_khqr_payment()
        self.assertEqual(move.khqr_status, "paid")
        self.assertEqual(move.payment_state, "paid")
