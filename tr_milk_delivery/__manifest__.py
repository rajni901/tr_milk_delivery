{
    'name': 'Milk Delivery Management',
    'version': '19.0.3.0.0',
    'category': 'Inventory/Delivery',
    'summary': 'Complete milk & dairy subscription delivery — routes, stop sequence, wallet, auto-schedule, holidays, WhatsApp.',
    'description': """
Milk Delivery Management — by Technical Rajni
=============================================
Full dairy delivery solution for milk rounds, dairy farms, and subscription delivery businesses.

Features:
- Delivery Routes with assigned drivers and active days
- Customer Subscriptions (product, qty, delivery days, active/paused/cancelled)
- Route Stop Sequence — drag-and-drop ordering for driver's daily route
- Daily Delivery Sheet auto-generated from active subscriptions
- Mark deliveries: Delivered / Skipped / Absent
- Customer Wallet / Prepaid Balance — auto-deduct on delivery
- Holiday & Vacation Management — skip deliveries on configured dates
- Auto-Schedule Cron — generate sheets automatically at 5am daily
- Delivery Calendar View — visual overview of all routes
- Auto-Invoice from confirmed deliveries (weekly/monthly)
- Printable PDF delivery sheet per route for drivers
- WhatsApp notification to customer on delivery (requires tr_whatsapp_notifications)
    """,
    'author': 'Technical Rajni',
    'website': 'https://www.technicalrajni.com',
    'license': 'OPL-1',
    'depends': ['sale_management', 'account', 'stock', 'mail', 'website', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/ir_cron.xml',
        'views/tr_milk_route_views.xml',
        'views/tr_milk_subscription_views.xml',
        'views/tr_milk_delivery_sheet_views.xml',
        'views/tr_milk_delivery_views.xml',
        'views/tr_milk_wallet_views.xml',
        'views/tr_milk_holiday_views.xml',
        'wizard/generate_delivery_sheet_views.xml',
        'wizard/create_invoices_views.xml',
        'report/delivery_sheet_report.xml',
        'report/delivery_sheet_template.xml',
        'views/menu.xml',
        'views/templates/driver_portal_template.xml',
        'views/templates/customer_portal_template.xml',
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
    'price': 79.00,
    'currency': 'USD',
}
