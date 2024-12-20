# Copyright 2024 Bernat Obrador
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class StockPicking(models.Model):
    _inherit = ["stock.picking"]

    def button_validate(self):
        """Override to generate analytic lines when stock moves are done."""
        res = super().button_validate()

        stock_analytic_model = self.env["stock.analytic.model"]
        for move_id in self.move_ids:
            stock_analytic_model.generate_analytic_lines(move_id)

        return res
