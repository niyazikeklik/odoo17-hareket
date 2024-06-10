{
    'name': 'Odoo Oracle Connection Provider',
    'category': 'Others',
    'depends': ['mail'],
    'version': '16.0',
    'description': """Odoo Oracle Connection Provider""",
    'summary': """Odoo Oracle Connection Provider""",
    'author': 'Mimol Yazılım',
    'maintainer': 'Mimol Yazılım',
    'company': 'Mimol Yazılım',
    'price': 9.99,
    'website': 'https://www.mimol.com.tr',
    "support": "info@mimol.com.tr",
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/res_users_views.xml',
        'views/oracle_pool_views.xml'
    ],
    'assets': {
        'web.assets_backend': []
    },
    'installable': True,
    'application': False,
    'license': 'OPL-1',
    'external_dependencies': {'python' : ['cx-Oracle']}
}
