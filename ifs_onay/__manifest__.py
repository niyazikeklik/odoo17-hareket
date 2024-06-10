{
    'name': 'IFS Onay',
    'category': 'Others',
    'depends': ['mail'],
    'version': '17.0',
    'description': """IFS Onay""",
    'summary': """IFS Onay""",
    'author': 'Mimol Yazılım',
    'maintainer': 'Mimol Yazılım',
    "company": 'Mimol Yazılım',
    "price": 999.99,
    "website": 'https://www.mimol.com.tr',
    "support": "info@mimol.com.tr",
    "data": [
        'security/ir.model.access.csv',
        'wizard/sas_baslik_reject_wizard_views.xml',
        'views/sas_baslik_views.xml',
        'views/sas_red_kodu_views.xml',
        'views/ifs_onay_menuitem_views.xml',
        'views/sas_onay_tarihce_views.xml',
        'data/ir_cron.xml',
        'data/activity_types_data.xml',
        'security/ir_rule.xml'
    ],
    'assets': {
        'web.assets_backend': []
    },
    'installable': True,
    'application': True,
    'license': 'OPL-1',
    'external_dependencies': {'python' : ['cx-Oracle']}
}
