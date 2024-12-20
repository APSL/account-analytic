# Copyright 2024 Bernat Obrador
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import datetime

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestStockAnalyticModel(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.analytic_plan = cls.env["account.analytic.plan"].create(
            {"name": "Test Plan"}
        )
        cls.stock_location = cls.env["stock.location"].create({"name": "Test Location"})
        cls.stock_location_2 = cls.env["stock.location"].create(
            {"name": "Test Location 2"}
        )
        cls.product_category = cls.env["product.category"].create(
            {"name": "Test Category"}
        )
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {"name": "Test Analytic Account", "plan_id": cls.analytic_plan.id}
        )
        cls.outgoing_picking_type = cls.env.ref("stock.picking_type_out")

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "categ_id": cls.product_category.id,
                "list_price": 100.0,
                "product_weight": 20.0,
            }
        )

    def _validate_analytic_lines_generated(self, analytic_lines, amount):
        account_id_field = self.analytic_plan._column_name()

        self.assertEqual(len(analytic_lines), 2)
        self.assertEqual(analytic_lines[0].amount, -amount)
        self.assertEqual(analytic_lines[1].amount, amount)
        self.assertEqual(analytic_lines[0].product_id, self.product)
        self.assertEqual(analytic_lines[1].product_id, self.product)
        self.assertEqual(
            getattr(analytic_lines[0], account_id_field), self.analytic_account
        )
        self.assertEqual(
            getattr(analytic_lines[1], account_id_field), self.analytic_account
        )

    def test_unique_combination_constraint(self):
        """
        Tests that creating a stock analytic model with a duplicate combination of
        location_from_id, location_dest_id, and product_category_id raises a
        ValidationError.
        """
        self.env["stock.analytic.model"].create(
            {
                "name": "Test Model",
                "location_from_id": self.stock_location.id,
                "location_dest_id": self.stock_location_2.id,
                "product_category_id": self.product_category.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.env["stock.analytic.model"].create(
                {
                    "name": "Test Model 2",
                    "location_from_id": self.stock_location.id,
                    "location_dest_id": self.stock_location_2.id,
                    "product_category_id": self.product_category.id,
                }
            )

    def test_create_analytic_lines_with_stock_picking(self):
        """
        Tests the creation of analytic lines for a stock analytic model when a stock
        picking is validated.
        """
        self.env["stock.analytic.model"].create(
            {
                "name": "Test Model",
                "location_from_id": self.stock_location.id,
                "location_dest_id": self.stock_location_2.id,
                "product_category_id": self.product_category.id,
                "positive_analytic_account_id": self.analytic_account.id,
                "negative_analytic_account_id": self.analytic_account.id,
                "avg_cost_per_kg": 10.0,
            }
        )
        picking_data = {
            "picking_type_id": self.outgoing_picking_type.id,
            "move_type": "direct",
            "location_id": self.stock_location.id,
            "location_dest_id": self.stock_location_2.id,
        }

        picking = self.env["stock.picking"].create(picking_data)

        move_data = {
            "picking_id": picking.id,
            "product_id": self.product.id,
            "location_id": self.stock_location.id,
            "location_dest_id": self.stock_location_2.id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date_deadline": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "name": self.product.name,
            "product_uom": self.product.uom_id.id,
            "product_uom_qty": 1.0,
        }

        self.env["stock.move"].create(move_data)

        picking.action_confirm()
        picking.action_assign()
        picking.button_validate()

        analytic_lines = self.env["account.analytic.line"].search(
            [("name", "=", "Test Model")]
        )

        self._validate_analytic_lines_generated(analytic_lines, 300.0)
