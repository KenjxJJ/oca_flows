# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class OCAFlows(models.Model):
    _name = 'oca.flows'
    _description = 'Odoo Extension for OCA Flow Management'

    name = fields.Char(string='Flow Name')
    description = fields.Text(string='Description')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    duration = fields.Integer(string='Duration')

    is_active = fields.Boolean(string='Active', default=True)
    activity_checklist = fields.Html(string='Activity Checklist')
    requires_prereq = fields.Boolean(string='Requires Prerequisites')

    @api.constrains('start_date', 'end_date')
    def _check_start_date(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.start_date > rec.end_date:
                raise UserError('Start Date must be before End Date!')

