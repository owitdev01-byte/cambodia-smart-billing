import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..services.nbc_service import fetch_nbc_usd_khr_rate

_logger = logging.getLogger(__name__)


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

    applied = fields.Boolean(
        string="Applied to Odoo",
        default=False,
        readonly=True,
        copy=False,
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

    def _cron_sync_nbc_rate(self):
        khr = self.env.ref("base.KHR", raise_if_not_found=False)
        usd = self.env.ref("base.USD", raise_if_not_found=False)
        if not khr or not usd:
            _logger.warning("KHR or USD currency not found; skipping NBC rate sync.")
            return

        rate = fetch_nbc_usd_khr_rate()
        if rate is None:
            return

        today = fields.Date.context_today(self)
        companies = self.env["res.company"].sudo().search([("currency_id", "=", usd.id)])
        for company in companies:
            existing = self.sudo().search([
                ("rate_date", "=", today),
                ("currency_id", "=", khr.id),
                ("company_id", "=", company.id),
            ], limit=1)
            if existing:
                existing.exchange_rate = rate
            else:
                self.sudo().create({
                    "rate_date": today,
                    "currency_id": khr.id,
                    "company_id": company.id,
                    "exchange_rate": rate,
                    "note": "Auto-synced from the National Bank of Cambodia.",
                })

    def action_apply_to_odoo(self):
        usd = self.env.ref("base.USD")
        for rec in self:
            if rec.company_id.currency_id != usd:
                raise UserError(_(
                    "This rate assumes the company's currency is USD (NBC publishes "
                    "KHR per 1 USD). %(company)s uses %(currency)s.",
                    company=rec.company_id.name,
                    currency=rec.company_id.currency_id.name,
                ))

            rate_model = self.env["res.currency.rate"].sudo()
            existing = rate_model.search([
                ("currency_id", "=", rec.currency_id.id),
                ("company_id", "=", rec.company_id.id),
                ("name", "=", rec.rate_date),
            ], limit=1)
            if existing:
                existing.company_rate = rec.exchange_rate
            else:
                rate_model.create({
                    "currency_id": rec.currency_id.id,
                    "company_id": rec.company_id.id,
                    "name": rec.rate_date,
                    "company_rate": rec.exchange_rate,
                })
            rec.applied = True