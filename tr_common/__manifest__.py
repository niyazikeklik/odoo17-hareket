# -*- coding: utf-8 -*-
{
    'name': "tr_common",
    'version': '16.0.1',
    'category': '',
    'sequence': 10,
    'summary': """TR Temel""",
    'description': """Şirket Temel - Mimol Yazılım""",
    'author': "Mimol YAZILIM",
    'website': "https://www.mimol.com.tr",
    'depends': ['base','mail'],
    'data': [
        'views/tr_company_views.xml',
        'security/ir.model.access.csv'
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
        ],
        'web.assets_qweb': [
        ],
    },
    'license': 'LGPL-3',
}
