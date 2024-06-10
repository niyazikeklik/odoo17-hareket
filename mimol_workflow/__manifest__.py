# -*- coding: utf-8 -*-
{
    'name': "mimol_workflow",
    'version': '15.0.1',
    'category': '',
    'sequence': 10,
    'summary': """Mimol Workflow engine""",
    'description': """Mimol Workflow engine""",
    'author': "Mimol YAZILIM",
    'website': "https://www.mimol.com.tr",
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/mimol_workflow_reject_wizard_views.xml'
    ],
    'demo': [
        'demo/demo.xml',
    ],
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
