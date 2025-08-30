from odoo import fields, models, api


class OCAEmployees(models.Model):
    _name = 'oca.employees'
    _description = 'OCA Workers/Employees'
    _inherit = 'hr.employee'

    category_ids = fields.Many2many(
        'hr.employee.category',
        'oca_employees_category_rel',
        'oca_employees_id',
        'category_id',
        string='Tags',

    )

    qualifications = fields.Many2many(
        'oca.employee.qualifications',
        'oca_employees_qualifications_rel',
        'oca_employees_id',
        'qualifications_id',
        string='Qualifications',
    )


class OCAQualifications(models.Model):
    _name = 'oca.employee.qualifications'
    _description = 'Employee Qualifications'


    employee_ids = fields.Many2many(
        'hr.employee',
        'oca_employees_qualifications_rel',
        'qualifications_id',
        'oca_employees_id',
        string='Employees',
    )