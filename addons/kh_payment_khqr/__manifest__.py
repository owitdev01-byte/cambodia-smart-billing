{
    "name": "Cambodia KHQR Payment",
    "version": "19.0.1.0.0",
    "category": "Accounting/Payment",
    "summary": "Attach uploaded KHQR codes to invoices with manual payment confirmation and reconciliation",
    "author": "Sambath & Kimnam",
    "license": "LGPL-3",
    "depends": ["account", "kh_currency_nbc"],
    "data": [
        "views/account_move_views.xml",
        "report/invoice_khqr_report.xml",
    ],
    "installable": True,
    "application": False,
}