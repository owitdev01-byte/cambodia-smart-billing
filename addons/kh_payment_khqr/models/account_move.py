import base64
import io

import qrcode
import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

from .khqr_builder import build_khqr_payload, khqr_md5

BAKONG_CHECK_TRANSACTION_URL = "https://api-bakong.nbc.gov.kh/v1/check_transaction_by_md5"


class AccountMove(models.Model):
    _inherit = "account.move"

    khqr_string = fields.Char(string="KHQR Payload", readonly=True, copy=False)
    khqr_md5 = fields.Char(string="KHQR MD5", readonly=True, copy=False)
    khqr_qr_image = fields.Binary(string="KHQR Code", compute="_compute_khqr_qr_image")
    khqr_status = fields.Selection(
        [("none", "Not Generated"), ("pending", "Pending Payment"), ("paid", "Paid")],
        string="KHQR Status",
        default="none",
        copy=False,
        tracking=True,
    )

    def _compute_khqr_qr_image(self):
        for move in self:
            if not move.khqr_string:
                move.khqr_qr_image = False
                continue
            image = qrcode.make(move.khqr_string)
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            move.khqr_qr_image = base64.b64encode(buffer.getvalue())

    def action_generate_khqr(self):
        self.ensure_one()
        if self.move_type != "out_invoice":
            raise UserError(_("KHQR codes can only be generated for customer invoices."))
        if self.state != "posted":
            raise UserError(_("Post the invoice before generating a KHQR code."))
        if self.currency_id.name not in ("USD", "KHR"):
            raise UserError(_("KHQR only supports USD or KHR invoices."))

        company = self.company_id
        if not company.bakong_account_id:
            raise UserError(_("Set a Bakong Account ID on the company before generating KHQR codes."))

        payload = build_khqr_payload(
            bakong_account_id=company.bakong_account_id,
            merchant_name=company.name,
            merchant_city=company.bakong_merchant_city or "Phnom Penh",
            amount=self.amount_residual,
            currency=self.currency_id.name,
            bill_number=self.name,
            merchant_category_code=company.bakong_merchant_category_code or "5999",
        )
        self.write({
            "khqr_string": payload,
            "khqr_md5": khqr_md5(payload),
            "khqr_status": "pending",
        })

    def action_check_khqr_payment(self):
        self.ensure_one()
        if not self.khqr_md5:
            raise UserError(_("Generate a KHQR code first."))

        token = self.company_id.bakong_api_token
        if not token:
            raise UserError(_("Set a Bakong API Token on the company to check payment status."))

        try:
            response = requests.post(
                BAKONG_CHECK_TRANSACTION_URL,
                json={"md5": self.khqr_md5},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise UserError(_("Could not reach Bakong: %s") % exc)

        data = response.json()
        if data.get("responseCode") == 0:
            self._register_khqr_payment()
        else:
            raise UserError(_("Payment not yet received."))

    def _register_khqr_payment(self):
        self.ensure_one()
        payment_register = self.env["account.payment.register"].with_context(
            active_model="account.move",
            active_ids=self.ids,
        ).create({
            "payment_date": fields.Date.context_today(self),
        })
        payment_register._create_payments()
        self.khqr_status = "paid"
