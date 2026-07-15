from odoo import api, fields, models


class NBCExchangeRate(models.Model):
    _name = "kh.currency.nbc"
    _description = "Cambodia Exchange Rate"
    _order = "rate_date desc"

    name = fields.Char(
        compute="_compute_name",
        store=True,
    )

    rate_date = fields.Date(
        string="Rate Date",
        required=True,
        default=fields.Date.context_today,
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )

    exchange_rate = fields.Float(
        string="Exchange Rate (KHR per 1 Unit)",
        digits=(12, 6),
        required=True,
    )

    note = fields.Text(
        string="Remark",
    )

    _sql_constraints = [
        (
            "unique_rate_per_day",
            "unique(rate_date, currency_id, company_id)",
            "An exchange rate for this currency already exists on this date.",
        )
    ]

    @api.depends("currency_id", "rate_date")
    def _compute_name(self):
        for rec in self:
            if rec.currency_id and rec.rate_date:
                rec.name = f"{rec.currency_id.name} - {rec.rate_date}"
            else:
                rec.name = "New"