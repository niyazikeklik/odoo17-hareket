# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'TR User and Employee Base',
    'version': '1.0',
    'category': 'Base',
    'sequence': -50,
    'summary': 'TR User and Employee Base',
    'description': "TR User and Employee Base",
    'website': 'https://www.mimol.com.tr',
    'images': ["static/description/banner.gif"],
    'depends': [
        'auth_ldap',
        'mail',
        'tr_common',
        'hr',
        'base_setup',
        'web'
    ],
    'data': [
             'views/tr_employee_inherit.xml',
             'security/ir.model.access.csv',
             'views/hr_department_views.xml',
             'views/res_currency_views.xml',
             'data/ir_cron.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
        ],
        'web.assets_qweb': [
        ],
        'web.assets_frontend': [
            'auth_signup/static/**/*',
        ]
    },
    'license': 'LGPL-3'
}

