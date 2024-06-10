{
    'name': 'Türkiye E-Mutabakat - IFS Bağlantısı',
    'category': 'Accounting/Accounting',
    'depends': ['tr_mutabakat','odoo_oracle','base_ifs'],
    'version': '16.0',
    'description': 'Türkiye E-Mutabakat IFS Bağlantısı',
    'summary': 'Türkiye E-Mutabakat IFS Bağlantısı',
    'author': 'Mimol Yazılım',
    'maintainer': 'Mimol Yazılım',
    'company': 'Mimol Yazılım',
    'price': 99,
    'website': 'https://www.mimol.com.tr',
    "support": "info@mimol.com.tr",
    'data': [
        'report/tr_cari_ekstre.xml',
        'data/tr_mutabakat_ifs_mail_template_data.xml',
        'data/tr_mutabakat_ifs_survey_data.xml',
        'data/tr_mutabakat_ifs_cron.xml',
        'data/tr_mutabakat_ifs_survey_template.xml',
        'views/tr_mut_views.xml',
        'views/tr_mut_kf_views.xml',
        'views/tr_mut_kdv2_views.xml',
        'wizard/tr_mut_ifs_veri_cek_wizard_views.xml',
        'views/tr_mutabakat_ifs_menuitem_views.xml',
        'security/ir.model.access.csv'
    ],
    'assets': {
        'web.assets_backend': []
    },
    'installable': True,
    'application': False,
    'license': 'OPL-1',
}
