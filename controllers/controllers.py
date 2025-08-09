# -*- coding: utf-8 -*-
# from odoo import http


# class Custom-addons/ocaFlows(http.Controller):
#     @http.route('/custom-addons/oca_flows/custom-addons/oca_flows', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom-addons/oca_flows/custom-addons/oca_flows/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom-addons/oca_flows.listing', {
#             'root': '/custom-addons/oca_flows/custom-addons/oca_flows',
#             'objects': http.request.env['custom-addons/oca_flows.custom-addons/oca_flows'].search([]),
#         })

#     @http.route('/custom-addons/oca_flows/custom-addons/oca_flows/objects/<model("custom-addons/oca_flows.custom-addons/oca_flows"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom-addons/oca_flows.object', {
#             'object': obj
#         })

