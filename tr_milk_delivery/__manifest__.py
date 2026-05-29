{
    'name': 'Milk Delivery Management',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Delivery',
    'summary': 'Complete milk & dairy subscription delivery management — routes, subscriptions, daily sheets, auto-invoicing.',
    'description': """
Milk Delivery Management — by Technical Rajni
=============================================
Full dairy delivery solution for milk rounds, dairy farms, and subscription delivery businesses.

Features:
- Delivery Routes with assigned drivers and active days
- Customer Subscriptions (product, qty, delivery days, active/paused/cancelled)
- Daily Delivery Sheet auto-generated from active subscriptions
- Mark deliveries: Delivered / Skipped / Absent
- Auto-Invoice at end of week or month from confirmed deliveries
- Printable PDF delivery sheet per route for drivers
- Dashboard: today's deliveries, active subscriptions, pending invoices
    """,
    'author': 'Technical Rajni',
    'website': 'https://www.technicalrajni.com',
    'license': 'OPL-1',
    'depends': ['sale_management', 'account', 'stock', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/tr_milk_route_views.xml',
        'views/tr_milk_subscription_views.xml',
        'views/tr_milk_delivery_sheet_views.xml',
        'views/tr_milk_delivery_views.xml',
        'wizard/generate_delivery_sheet_views.xml',
        'wizard/create_invoices_views.xml',
        'report/delivery_sheet_report.xml',
        'report/delivery_sheet_template.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tr_milk_delivery/static/src/css/milk_delivery.css',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 29.00,
    'currency': 'USD',
}
