{
    'name': 'Masraf Modülü',
    'category': 'Others',
    'depends': ['mail','tr_common','hr'],
    'version': '17.0',
    'description': """Hareket Masraf Modülü""",
    'summary': """Hareket Masraf Modülü""",
    'author': 'Mimol Yazılım',
    'maintainer': 'Mimol Yazılım',
    "company": 'Mimol Yazılım',
    "website": 'https://www.mimol.com.tr',
    "support": "info@mimol.com.tr",
    "data": [
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'wizard/harkt_para_talep_reject_wizard_views.xml',
        'views/harkt_detay_views.xml',
        'views/harkt_kdv_views.xml',
        'views/harkt_masraf_ongrup_views.xml',
        'views/harkt_masraf_turu_views.xml',
        'views/harkt_muhasebe_kodu_views.xml',
        'views/harkt_para_talep_views.xml',
        'views/harkt_masraf_views.xml',
        'views/harkt_proje_views.xml',
        'views/harkt_aktivite_views.xml',
        'views/harkt_nakit_hesap_views.xml',
        'views/tr_company_views.xml',
        'views/harkt_masraf_menuitem_views.xml',
        'data/ir_cron.xml'
    ],
    'assets': {
        'web.assets_backend': []
    },
    'installable': True,
    'application': True,
    'license': 'OPL-1'
}
