# Copyright 2024 Bernat Obrador
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = ["account.analytic.line"]

    stock_move_id = fields.Many2one("stock.move", string="Stock Move")
