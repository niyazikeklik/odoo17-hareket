{
    'name': 'Türkiye E-Mutabakat Sistemi',
    'icon': '/l10n_tr/static/description/icon.png',
    'category': 'Accounting/Accounting',
    'depends': ['mail', 'survey', 'mm_survey_attachment'],
    'version': '16.0',
    'description': 'Türkiye E-Mutabakat Sistemi',
    'summary': 'Türkiye E-Mutabakat Sistemi',
    'author': 'Mimol Yazılım',
    'maintainer': 'Mimol Yazılım',
    'company': 'Mimol Yazılım',
    'price': 499,
    'website': 'https://www.mimol.com.tr',
    "support": "info@mimol.com.tr",
    'data': [
        'security/tr_mut_security.xml',
        'security/ir.model.access.csv',
        'data/tr_mutabakat_mail_template_data.xml',
        'data/tr_mutabakat_survey_data.xml',
        'data/tr_mutabakat_survey_template.xml',
        'views/tr_mut_views.xml',
        'views/tr_mutabakat_menuitem_views.xml'
    ],
    'assets': {
        'web.assets_backend': []
    },
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}
