# Copyright 2024 Bernat Obrador
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock Analytic Distribution Model",
    "summary": "Adds distribution models for stock moves",
    "version": "17.0.1.2.0",
    "author": "APSL-Nagarro",
    "website": "https://github.com/OCA/account-analytic",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "depends": ["stock", "account", "product_logistics_uom"],
    "data": [
        "views/stock_analytic_model.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
