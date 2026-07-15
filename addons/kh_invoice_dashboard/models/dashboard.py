from odoo import api, fields, models


class KhInvoiceDashboard(models.Model):
    _name = "kh.invoice.dashboard"
    _description = "KH Invoice Dashboard"

    name = fields.Char(default="Invoice Dashboard")

    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        readonly=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        readonly=True,
    )

    total_invoice = fields.Integer(compute="_compute_dashboard")
    draft_invoice = fields.Integer(compute="_compute_dashboard")
    posted_invoice = fields.Integer(compute="_compute_dashboard")
    paid_invoice = fields.Integer(compute="_compute_dashboard")
    overdue_invoice = fields.Integer(compute="_compute_dashboard")

    total_sales = fields.Monetary(
        currency_field="currency_id",
        compute="_compute_dashboard",
    )

    outstanding_amount = fields.Monetary(
        currency_field="currency_id",
        compute="_compute_dashboard",
    )

    last_updated = fields.Datetime(compute="_compute_dashboard")

    def _compute_dashboard(self):

        today = fields.Date.today()

        for rec in self:

            invoices = self.env["account.move"].search([
                ("move_type", "=", "out_invoice"),
                ("company_id", "=", rec.company_id.id),
            ])

            rec.total_invoice = len(invoices)

            rec.draft_invoice = len(
                invoices.filtered(lambda m: m.state == "draft")
            )

            rec.posted_invoice = len(
                invoices.filtered(lambda m: m.state == "posted")
            )

            rec.paid_invoice = len(
                invoices.filtered(lambda m: m.payment_state == "paid")
            )

            rec.overdue_invoice = len(
                invoices.filtered(
                    lambda m:
                        m.state == "posted"
                        and m.payment_state != "paid"
                        and m.invoice_date_due
                        and m.invoice_date_due < today
                )
            )

            posted = invoices.filtered(lambda m: m.state == "posted")

            rec.total_sales = sum(posted.mapped("amount_total"))

            outstanding = posted.filtered(
                lambda m: m.payment_state != "paid"
            )

            rec.outstanding_amount = sum(
                outstanding.mapped("amount_residual")
            )

            rec.last_updated = fields.Datetime.now()