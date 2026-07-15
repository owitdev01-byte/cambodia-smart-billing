{
    "name": "Khmer Invoice Dashboard",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "summary": "A dashboard for Khmer invoices",
    "author": "Sambath & Kimnam",
    "license": "LGPL-3",
    "depends": ["base", "account"],
    "data": [
        "security/ir.model.access.csv",
        "data/dashboard_data.xml",
        "views/dashboard_views.xml",
        "views/menu.xml"
    ],
    "installable": True,
    "application": True,    
}