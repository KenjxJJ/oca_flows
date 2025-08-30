from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_oca_customer = fields.Boolean(string='OCA Customer?')
