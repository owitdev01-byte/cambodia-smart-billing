from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    bakong_account_id = fields.Char(string="Bakong Account ID")
    bakong_merchant_city = fields.Char(string="Bakong Merchant City", default="Phnom Penh")
    bakong_merchant_category_code = fields.Char(string="Merchant Category Code", default="5999")
    bakong_api_token = fields.Char(string="Bakong API Token", groups="base.group_system")
