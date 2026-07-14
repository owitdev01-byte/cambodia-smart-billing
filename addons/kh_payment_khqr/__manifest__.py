{
    "name": "Cambodia KHQR Payment",
    "version": "19.0.1.0.0",
    "category": "Accounting/Payment",
    "summary": "Generate KHQR codes on invoices with payment confirmation and reconciliation",
    "author": "Sambath & Kimnam",
    "license": "LGPL-3",
    "depends": ["account", "kh_currency_nbc"],
    "data": [
        "views/account_move_views.xml",
        "views/res_company_views.xml",
        "report/invoice_khqr_report.xml",
    ],
    "external_dependencies": {
        "python": ["qrcode", "requests"],
    },
    "installable": True,
    "application": False,
}