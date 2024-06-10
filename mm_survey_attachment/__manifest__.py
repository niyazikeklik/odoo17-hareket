{
    'name': 'Survey Attachment Question',

    'summary': 'Adds new File Question type, uploaded file stored in answers, survey attachment',

    'author': 'Mimol Yazılım',
    'website': 'https://www.mimol.com.tr',

    'category': 'Other Category',
    'license': 'OPL-1',
    'version': '16.0.1',
    'depends': [
        'survey', 'mail'
    ],
    'data': [
        'views/survey_template_view.xml',
        'views/survey_user_input_line_view.xml',
        'views/survey_view.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'mm_survey_attachment/static/src/js/url_widget.js',
            'mm_survey_attachment/static/src/js/survey_form.js'
        ]
    },
    'installable': True

}
