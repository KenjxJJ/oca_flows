# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class OCAFlows(models.Model):
    _name = 'oca.flows'
    _description = 'OCA Flows Description'

    name = fields.Char(string='Flow Name')
    description = fields.Text(string='Description')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    duration = fields.Integer(string='Duration')

    is_active = fields.Boolean(string='Active', default=True)
    activity_checklist = fields.Html(string='Activity Checklist')
    requires_prereq = fields.Boolean(string='Requires Prerequisites')

    request_ids = fields.One2many('oca.process.requests', 'flow_id', string='Customer Requests')
    customer_ids = fields.Many2many('res.partner', string='Customers')

    @api.constrains('start_date', 'end_date')
    def _check_start_date(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.start_date > rec.end_date:
                raise UserError('Start Date must be before End Date!')

    requests_count = fields.Integer(compute='_compute_requests_count')

    def _compute_requests_count(self):
        # aggregate counts by flow_id in one query
        data = self.env['oca.process.requests'].read_group(
            [('flow_id', 'in', self.ids)],
            fields=['flow_id'],
            groupby=['flow_id'],
        )
        counts = {d['flow_id'][0]: d['flow_id_count'] for d in data}
        for rec in self:
            rec.requests_count = counts.get(rec.id, 0)

    def action_open_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Request Submissions',
            'res_model': 'oca.process.requests',
            'view_mode': 'list,form',
            'domain': [('flow_id', '=', self.id)],
        }

    def _sync_customers_from_request(self):
        Requests = self.env['oca.process.requests'].sudo()
        for rec in self:
            partner_ids = Requests.search([
                ('flow_id', '=', rec.id),
                ('state', 'in', ('approved', 'in_progress', 'completed'))
            ]).mapped('customer_id').ids
            rec.write({'customer_ids': [(6, 0, partner_ids)]})


class OCAProcess(models.Model):
    _name = 'oca.process.requests'
    _description = 'OCA Process Requests'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Process No.')
    description = fields.Text(string='Description')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    duration = fields.Integer(string='Duration')

    customer_id = fields.Many2one('res.partner', string='Customer')
    flow_id = fields.Many2one('oca.flows', string='Flow')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.mapped('flow_id')._sync_customers_from_request()
        return records

    def write(self, vals):
        res = super().write(vals)
        self.mapped('flow_id')._sync_customers_from_request()
        return res

    def unlink(self):
        processes = self.mapped('flow_id')
        res = super().unlink()
        processes._sync_customers_from_request()
        return res

    def action_submit(self):
        for rec in self:
            rec.write({'state': 'submitted'})

    def action_approve(self):
        for rec in self:
            rec.write({'state': 'approved'})

    def action_reject(self):
        for rec in self:
            rec.write({'state': 'rejected'})

    def action_cancel(self):
        for rec in self:
            rec.write({'state': 'cancelled'})

    def action_in_progress(self):
        for rec in self:
            rec.write({'state': 'in_progress'})

    def action_completed(self):
        for rec in self:
            rec.write({'state': 'completed'})
