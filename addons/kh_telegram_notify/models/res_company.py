from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    telegram_bot_token = fields.Char(string="Telegram Bot Token", groups="base.group_system")
    telegram_chat_id = fields.Char(string="Telegram Chat ID")
