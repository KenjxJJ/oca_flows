# -*- coding: utf-8 -*-
{
    'name': "OCA Flows Management",

    'summary': "Custom Flows for OCA Flow - Coffee Processing",
    'author': "KenjxJJ",
    'category': 'Manufacturing',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/oca_flow_views.xml',
        # 'views/templates.xml',
        'views/oca_process_requests.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'images': ['static/description/icon.png'],

}

