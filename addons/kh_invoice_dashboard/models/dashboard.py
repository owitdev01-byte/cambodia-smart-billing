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

    # KHR is always the same currency for every row, regardless of the
    # company's own currency — used purely to display the KHR-equivalent
    # amounts below with the correct symbol/formatting.
    currency_id_khr = fields.Many2one(
        "res.currency",
        string="Currency (KHR)",
        compute="_compute_currency_id_khr",
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

    total_sales_khr = fields.Monetary(
        string="Total Sales (KHR)",
        currency_field="currency_id_khr",
        compute="_compute_dashboard",
    )

    outstanding_amount_khr = fields.Monetary(
        string="Outstanding (KHR)",
        currency_field="currency_id_khr",
        compute="_compute_dashboard",
    )

    last_updated = fields.Datetime(compute="_compute_dashboard")

    def _compute_currency_id_khr(self):
        khr = self.env["res.currency"].search([("name", "=", "KHR")], limit=1)
        for rec in self:
            rec.currency_id_khr = khr.id if khr else False

    def _compute_dashboard(self):

        today = fields.Date.today()
        khr = self.env["res.currency"].search([("name", "=", "KHR")], limit=1)

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

            # KHR-equivalent amounts, converted via Odoo's own currency
            # rate table (Settings > Currencies). Falls back to the raw
            # amount if KHR isn't configured, rather than erroring out.
            if khr and rec.currency_id:
                rec.total_sales_khr = rec.currency_id._convert(
                    rec.total_sales, khr, rec.company_id, today
                )
                rec.outstanding_amount_khr = rec.currency_id._convert(
                    rec.outstanding_amount, khr, rec.company_id, today
                )
            else:
                rec.total_sales_khr = rec.total_sales
                rec.outstanding_amount_khr = rec.outstanding_amount

            rec.last_updated = fields.Datetime.now()