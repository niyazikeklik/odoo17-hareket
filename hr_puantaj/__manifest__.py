{
    'name': 'Personel Puantaj',
    'category': 'Others',
    'depends': ['base', 'web', 'mail','tr_common','hr','fleet','hr_work_entry','hr_contract','hr_work_entry_contract','hr_attendance'],
    'version': '17.0',
    'description': """Personel Puantaj Modülü""",
    'summary': """Personel Puantaj Modülü""",
    'author': 'Mimol Yazılım',
    'maintainer': 'Mimol Yazılım',
    "company": 'Mimol Yazılım',
    "website": 'https://www.mimol.com.tr',
    "support": "info@mimol.com.tr",
    "data": [
        #'views/hr_leave_type_views.xml',
        "views/hr_res_montaj_tipi_views.xml",
        'views/hr_work_entry_views.xml',
        "security/ir_rule.xml",
        "security/ir.model.access.csv",
        "data/geolocation_data.xml",
        "views/res_config_settings.xml",
        "views/hr_attendance_geofence.xml",
        "views/hr_attendance_views.xml",
        "views/hr_employee_views.xml",
        'wizards/hr_attendance_wizard_views.xml',
        'views/hr_puantaj_menuitem_views.xml'
    ],
    'assets': {
        "web.assets_backend": [
            # https://github.com/justadudewhohacks/face-api.js
            "/hr_puantaj/static/src/lib/faceapi/source/face-api.js",

            # Ol Steet Map
            "/hr_puantaj/static/src/lib/ol-6.12.0/ol.css",
            "/hr_puantaj/static/src/lib/ol-ext/ol-ext.css",
            "/hr_puantaj/static/src/lib/ol-6.12.0/ol.js",
            "/hr_puantaj/static/src/lib/ol-ext/ol-ext.js",

            "/hr_puantaj/static/src/js/*.*",
        ],
        "hr_attendance.assets_public_attendance":[
            # https://cdn.jsdelivr.net/npm/@vladmandic/human/dist/human.js
            "/hr_puantaj/static/src/lib/faceapi/source/face-api.js",

            # Ol Steet Map
            "/hr_puantaj/static/src/lib/ol-6.12.0/ol.css",
            "/hr_puantaj/static/src/lib/ol-ext/ol-ext.css",
            "/hr_puantaj/static/src/lib/ol-6.12.0/ol.js",
            "/hr_puantaj/static/src/lib/ol-ext/ol-ext.js",

            "/hr_puantaj/static/src/js/attendance_recognition_dialog.js",
            "/hr_puantaj/static/src/js/attendance_recognition_dialog.xml",
            "/hr_puantaj/static/src/js/public_kiosk_app.scss",
            "/hr_puantaj/static/src/js/public_kiosk_app.js",
            "/hr_puantaj/static/src/js/public_kiosk_app.xml",
        ]
    },
    'installable': True,
    'application': True,
    'license': 'OPL-1',
    "pre_init_hook" :  "pre_init_check",
}
