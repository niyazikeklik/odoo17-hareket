{
    'name': 'Message Filter',
    'description': 'Filter messages based on domain',
    
    'version': '1.0',
    'application': True,
    'data': [
        'views/message_filter.xml',
        'security/ir.model.access.csv',
    ],
    'depends': ['base', 'mail'],

}