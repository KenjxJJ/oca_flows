# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class OCAFlows(models.Model):
    _name = 'oca.flows'
    _description = 'OCA Flows Description'
    _inherits = {'product.product': 'product_id'}

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        ondelete='cascade',
        help='Underlying product used for sales/invoicing.'
    )

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    duration = fields.Integer(string='Duration (Days)', compute='_compute_duration', store=True)

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

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                rec.duration = (rec.end_date - rec.start_date).days
            else:
                rec.duration = 0

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

    name = fields.Char(string='Process No.', copy=False, readonly=True)
    description = fields.Html(string='Description')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    duration = fields.Integer(string='Duration (Days)')
    price = fields.Float(string='Price')

    customer_id = fields.Many2one('res.partner', string='Customer')
    flow_id = fields.Many2one('oca.flows', string='Flow')
    activity_checklist = fields.Html(related='flow_id.activity_checklist')
    sale_quotation_ids = fields.One2many('sale.order', 'process_id', string='Customer Quotes')
    sale_quotation_count = fields.Integer(compute='_compute_sale_quotation_count')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        compute='_compute_currency_id', store=True, readonly=False, precompute=True,
        help="The payment's currency.")
    approved_by = fields.Many2one('res.users', string='Approved By')
    approved_on = fields.Date(string='Approved Date')

    @api.depends('pricelist_id', 'company_id')
    def _compute_currency_id(self):
        for req in self:
            req.currency_id = req.pricelist_id.currency_id or req.company_id.currency_id

    def _set_pricelist_id(self):
        for rec in self:
            rec.pricelist_id = self.env['product.pricelist'].search([
                '|', ('company_id', '=', False),
                ('company_id', '=', self.env.company.id)], limit=1)

    @api.onchange('flow_id')
    def _onchange_flow_id(self):
        for rec in self:
            if rec.flow_id:
                self._set_pricelist_id()

                rec.start_date = rec.flow_id.start_date
                rec.end_date = rec.flow_id.end_date
                rec.duration = rec.flow_id.duration
                rec.description = rec.flow_id.description
                rec.price = rec.flow_id.list_price

    @api.model_create_multi
    def create(self, vals_list):
        # Ensure vals_list is a list of dictionaries
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        # Generate a unique sequence for each record
        for item in vals_list:
            seq = self.env['ir.sequence'].next_by_code('oca.flow.requests')
            if not seq:
                raise UserError("Unable to generate sequence for oca.flow.requests")
            item['name'] = seq

        # Call the parent create method to create records
        records = super().create(vals_list)

        # Sync to process list if flow_id exists
        if records.mapped('flow_id'):
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
            rec.write({
                'state': 'approved',
                'approved_by': self.env.user.id,
                'approved_on': fields.Date.today(),
            })

    def action_reject(self):
        for rec in self:
            rec.write({'state': 'rejected'})

    def action_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    def action_cancel(self):
        for rec in self:
            rec.write({'state': 'cancelled'})

    def action_in_progress(self):
        for rec in self:
            rec.write({'state': 'in_progress'})

    def action_completed(self):
        for rec in self:
            rec.write({'state': 'completed'})

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_id)

    def action_view_quotations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.sale_quotation_ids.ids)],
            'context': {'create': False},
        }

    def _compute_sale_quotation_count(self):
        for rec in self:
            rec.sale_quotation_count = len(rec.sale_quotation_ids)

    def action_create_quotation(self):
        self.ensure_one()

        if self.state != 'approved':
            raise UserError(_("Only approved applications can be invoiced."))

        if not self.customer_id:
            raise UserError(_("Customer is required to create a quotation."))

        if not self.flow_id or not self.flow_id.product_id:
            raise UserError(_("The selected process has no product attached."))

        # Company / Partner / Product context
        company = self.flow_id.company_id or self.env.company
        partner = self.customer_id.commercial_partner_id.with_company(company)
        product = self.flow_id.product_id.with_company(company)

        # Make sure partner is considered a customer
        if partner.customer_rank == 0:
            partner.customer_rank = 1

        # Price & currency (use partner pricelist if present)
        price_unit = self.flow_id.list_price or product.list_price or 0.0

        # Prepare invoice values
        quotation_vals = {
            'partner_id': partner.id,
            'date_order': fields.Date.context_today(self),
            'origin': self.name or _('RFQ'),
            'pricelist_id': partner.property_product_pricelist.id,
            'company_id': company.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'name': product.get_product_multiline_description_sale() or product.display_name,
                'product_uom_qty': 1.0,
                'price_unit': price_unit,
            })],
        }

        so = self.env['sale.order'].with_company(company).create(quotation_vals)
        self.sale_quotation_ids = [(4, so.id)]
        self.message_post(
            body=_(f"Quoatation {so.name} created and posted.")
        )

        # Open sales quotation
        return {
            'type': 'ir.actions.act_window',
            'name': _(f'Sale Quote{so.name}({partner.display_name})'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': so.id,
            'target': 'current',
        }

    class SaleOrder(models.Model):
        _inherit = 'sale.order'

        process_id = fields.Many2one('oca.process.requests', string='RFQs')
