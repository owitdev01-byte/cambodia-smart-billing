{
    "name": "Cambodia NBC Exchange Rate Sync",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "summary": "Daily KHR/USD exchange rate sync from the National Bank of Cambodia",
    "author": "Sambath & Kimnam",
    "license": "LGPL-3",
    "depends": ["base", "account"],
    "data": [
        "data/ir_cron.xml",
        "security/ir.model.access.csv",
        "views/nbc_exchange_rate_views.xml",
    ],
    "installable": True,
    "application": True,    
}