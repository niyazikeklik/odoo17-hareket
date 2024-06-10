{
    'name': 'Hareket Bakım Modülü',
    'category': 'Others',
    'depends': ['mail'],
    'version': '17.0',
    'description': """Hareket Bakım Modülü""",
    'summary': """Hareket Bakım Modülü""",
    'author': 'Mimol Yazılım',
    'maintainer': 'Mimol Yazılım',
    "company": 'Mimol Yazılım',
    "website": 'https://www.mimol.com.tr',
    "support": "info@mimol.com.tr",
    "data": [
        'views/maintenance_equipment_views.xml',
        'views/maintenance_request_views.xml',
    ],
    'assets': {
        'web.assets_backend': []
    },
    'installable': True,
    'application': True,
    'license': 'OPL-1'
}
