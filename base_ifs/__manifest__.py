{
    'name': 'Odoo IFS Bağlantısı',
    'category': 'Accounting/Accounting',
    'depends': ['base'],
    'version': '16.0',
    'description': 'Odoo Şirketi ile IFS Şirketini birbirine bağlar',
    'summary': 'Odoo IFS Bağlantısı',
    'author': 'Mimol Yazılım',
    'maintainer': 'Mimol Yazılım',
    'company': 'Mimol Yazılım',
    'price': 9,
    'website': 'https://www.mimol.com.tr',
    "support": "info@mimol.com.tr",
    'data': [
        'views/res_company_views.xml'
    ],
    'assets': {
        'web.assets_backend': []
    },
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}
