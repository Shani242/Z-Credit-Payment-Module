{
    'name': 'Z-Credit Payment Test',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Test Z-Credit payment gateway integration',
    'author': 'Developer',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/zcredit_transaction_views.xml',
    ],
    'installable': True,
    'application': True,
}