# Copyright 2024 Bernat Obrador
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class ReturnPicking(models.TransientModel):
    _inherit = ["stock.return.picking"]

    def _create_returns(self):
        """Override to generate analytic lines when returning stock pickings."""
        new_picking, picking_type_id = super()._create_returns()

        stock_picking = self.env["stock.picking"].browse(new_picking)

        stock_analytic_model = self.env["stock.analytic.model"]
        for move_id in stock_picking.move_ids:
            stock_analytic_model.generate_analytic_lines(move_id)

        return new_picking, picking_type_id
