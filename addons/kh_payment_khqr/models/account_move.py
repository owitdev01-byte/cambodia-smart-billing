from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    khqr_qr_image = fields.Binary(string="KHQR Code", copy=False)
    khqr_status = fields.Selection(
        [("none", "Not Uploaded"), ("pending", "Pending Payment"), ("paid", "Paid")],
        string="KHQR Status",
        default="none",
        copy=False,
        tracking=True,
    )

    @api.constrains("khqr_qr_image")
    def _check_khqr_upload_allowed(self):
        for move in self:
            if not move.khqr_qr_image:
                continue
            if move.move_type != "out_invoice":
                raise ValidationError(_("KHQR codes can only be attached to customer invoices."))
            if move.state != "posted":
                raise ValidationError(_("Post the invoice before attaching a KHQR code."))
            if move.currency_id.name not in ("USD", "KHR"):
                raise ValidationError(_("KHQR only supports USD or KHR invoices."))

    @api.onchange("khqr_qr_image")
    def _onchange_khqr_qr_image(self):
        if self.khqr_qr_image and self.khqr_status == "none":
            self.khqr_status = "pending"

    def action_confirm_khqr_payment(self):
        self.ensure_one()
        if not self.khqr_qr_image:
            raise UserError(_("Upload a KHQR code before marking payment as received."))

        payment_register = self.env["account.payment.register"].with_context(
            active_model="account.move",
            active_ids=self.ids,
        ).create({
            "payment_date": fields.Date.context_today(self),
        })
        payment_register._create_payments()
        self.khqr_status = "paid"
