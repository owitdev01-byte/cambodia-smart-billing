{
    "name": "Cambodia KHQR Telegram Notifications",
    "version": "19.0.1.0.0",
    "category": "Accounting/Payment",
    "summary": "Notify a Telegram chat when a KHQR invoice is uploaded or marked paid",
    "author": "Sambath & Kimnam",
    "license": "LGPL-3",
    "depends": ["kh_payment_khqr"],
    "data": [
        "views/res_company_views.xml",
    ],
    "external_dependencies": {
        "python": ["requests"],
    },
    "installable": True,
    "application": False,
}
