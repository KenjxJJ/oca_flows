# -*- coding: utf-8 -*-
{
    'name': "OCA Flows Management",

    'summary': "Custom Flows for OCA Flow",
    'description': """OCA Training from Tech Things """,
    'author': "KenjxJJ",
    'category': 'Accounting',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/oca_flow_views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

