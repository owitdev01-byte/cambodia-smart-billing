from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase, tagged

SAMPLE_HTML = """
<table><tr><td>
Official Exchange Rate : <font color="#FF3300">4037</font> KHR / USD
</td></tr></table>
"""


@tagged("post_install", "-at_install")
class TestNbcRateSync(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.usd = cls.env.ref("base.USD")
        cls.khr = cls.env.ref("base.KHR")
        cls.usd.active = True
        cls.khr.active = True
        cls.env.company.currency_id = cls.usd.id

    def _today_rate(self):
        return self.env["kh.currency.nbc"].search([
            ("currency_id", "=", self.khr.id),
            ("company_id", "=", self.env.company.id),
            ("rate_date", "=", fields.Date.context_today(self.env["kh.currency.nbc"])),
        ])

    @patch("odoo.addons.kh_currency_nbc.services.nbc_service.requests.get")
    def test_cron_creates_todays_rate(self, mock_get):
        mock_get.return_value.text = SAMPLE_HTML
        mock_get.return_value.raise_for_status.return_value = None

        self.env["kh.currency.nbc"]._cron_sync_nbc_rate()

        rate = self._today_rate()
        self.assertEqual(len(rate), 1)
        self.assertAlmostEqual(rate.exchange_rate, 4037.0, places=2)

    @patch("odoo.addons.kh_currency_nbc.services.nbc_service.requests.get")
    def test_cron_updates_existing_rate_same_day(self, mock_get):
        mock_get.return_value.text = SAMPLE_HTML
        mock_get.return_value.raise_for_status.return_value = None
        self.env["kh.currency.nbc"]._cron_sync_nbc_rate()

        mock_get.return_value.text = SAMPLE_HTML.replace("4037", "4050")
        self.env["kh.currency.nbc"]._cron_sync_nbc_rate()

        rate = self._today_rate()
        self.assertEqual(len(rate), 1)
        self.assertAlmostEqual(rate.exchange_rate, 4050.0, places=2)

    @patch("odoo.addons.kh_currency_nbc.services.nbc_service.requests.get")
    def test_no_record_created_when_page_unparseable(self, mock_get):
        mock_get.return_value.text = "<html>no rate here</html>"
        mock_get.return_value.raise_for_status.return_value = None

        self.env["kh.currency.nbc"]._cron_sync_nbc_rate()

        self.assertFalse(self._today_rate())

    @patch("odoo.addons.kh_currency_nbc.services.nbc_service.requests.get")
    def test_no_record_created_when_fetch_fails(self, mock_get):
        import requests as _requests
        mock_get.side_effect = _requests.RequestException("boom")

        self.env["kh.currency.nbc"]._cron_sync_nbc_rate()

        self.assertFalse(self._today_rate())
