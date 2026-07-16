from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    khqr_qr_image = fields.Binary(string="QR Code", copy=False)
    khqr_status = fields.Selection(
        [("none", "Not Uploaded"), ("pending", "Pending Payment"), ("paid", "Paid")],
        string="QR Status",
        default="none",
        copy=False,
        tracking=True,
    )

    alt_currency_id = fields.Many2one(
        "res.currency", string="Other Currency", compute="_compute_alt_currency_amount"
    )
    alt_amount_total = fields.Monetary(
        string="Total (Other Currency)",
        compute="_compute_alt_currency_amount",
        currency_field="alt_currency_id",
    )

    @api.depends("amount_total", "currency_id", "invoice_date")
    def _compute_alt_currency_amount(self):
        usd = self.env.ref("base.USD", raise_if_not_found=False)
        khr = self.env.ref("base.KHR", raise_if_not_found=False)
        for move in self:
            if usd and khr and move.currency_id in (usd, khr) and move.amount_total:
                other = khr if move.currency_id == usd else usd
                date = move.invoice_date or fields.Date.context_today(move)
                move.alt_currency_id = other
                move.alt_amount_total = move.currency_id._convert(
                    move.amount_total, other, move.company_id, date
                )
            else:
                move.alt_currency_id = False
                move.alt_amount_total = 0.0

    @api.constrains("khqr_qr_image")
    def _check_khqr_upload_allowed(self):
        for move in self:
            if not move.khqr_qr_image:
                continue
            if move.move_type != "out_invoice":
                raise ValidationError(_("QR codes can only be attached to customer invoices."))
            if move.state != "posted":
                raise ValidationError(_("Post the invoice before attaching a QR code."))
            if move.currency_id.name not in ("USD", "KHR"):
                raise ValidationError(_("This QR payment flow only supports USD or KHR invoices."))

    @api.onchange("khqr_qr_image")
    def _onchange_khqr_qr_image(self):
        if self.khqr_qr_image and self.khqr_status == "none":
            self.khqr_status = "pending"

    def action_confirm_khqr_payment(self):
        self.ensure_one()
        if not self.khqr_qr_image:
            raise UserError(_("Upload a QR code before marking payment as received."))

        payment_register = self.env["account.payment.register"].with_context(
            active_model="account.move",
            active_ids=self.ids,
        ).create({
            "payment_date": fields.Date.context_today(self),
        })
        payment_register._create_payments()
        self.khqr_status = "paid"
