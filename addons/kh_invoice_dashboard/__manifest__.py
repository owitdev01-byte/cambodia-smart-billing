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
        "views/kh_invoice_dashboard_views.xml",  # tree/form/search — must load FIRST
        "data/dashboard_data.xml",                 # action_kh_invoice_dashboard refs the search view above
        "views/dashboard_views.xml",                # OWL client action + root menu
        "views/menu.xml",                            # menuitem refs action_kh_invoice_dashboard above
    ],
    "assets": {
        "web.assets_backend": [
            "kh_invoice_dashboard/static/src/scss/invoice_dashboard.scss",
            "kh_invoice_dashboard/static/src/js/invoice_dashboard.js",
            "kh_invoice_dashboard/static/src/xml/invoice_dashboard.xml",
        ],
    },
    "installable": True,
    "application": True,    
}