# Copyright 2024 Bernat Obrador
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockAnalyticModel(models.Model):
    _name = "stock.analytic.model"
    _description = "Stock Analytic Model"

    name = fields.Char(required=True)
    location_from_id = fields.Many2one("stock.location", string="From", required=True)
    location_dest_id = fields.Many2one("stock.location", string="To", required=True)
    product_category_id = fields.Many2one(
        "product.category", string="Product Category", required=True
    )
    positive_analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Positive Analytic Account"
    )
    negative_analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Negative Analytic Account"
    )
    avg_cost_per_kg = fields.Float(
        string="Average Cost Per Kg",
        digits=(16, 2),
        help="""Represents the average cost per kilogram,
        used to calculate the delivery cost for generating analytic lines.""",
    )

    @api.constrains("location_from_id", "location_dest_id", "product_category_id")
    def _check_unique_combination(self):
        """
        This method ensures that the combination of 'From', 'To',
        and 'Product Category' is unique.
        """
        for record in self:
            duplicates = self.search(
                [
                    ("location_from_id", "=", record.location_from_id.id),
                    ("location_dest_id", "=", record.location_dest_id.id),
                    ("product_category_id", "=", record.product_category_id.id),
                    ("id", "!=", record.id),
                ]
            )
            if duplicates:
                raise ValidationError(
                    _(
                        """A Stock Analytic Model with the same 'From', 'To',
                        and 'Product Category' already exists."""
                    )
                )

    def _is_match(self, location_from_id, location_dest_id, product_category_id):
        """
        Checks if the model matches the given criteria.
        Criteria: location_from_id, location_dest_id, and product_category_id
        are the fields that needs to match.
        """
        return (
            self.location_from_id.id == location_from_id
            and self.location_dest_id.id == location_dest_id
            and self.product_category_id.id == product_category_id
        )

    def _compute_amount(self, product, quantity, avg_cost_per_kg):
        """
        Computes the amount for the analytic line.
        Formula: (price * quantity) + ((weight * quantity) * avg_cost_per_kg)
        """
        return product.list_price * quantity + (
            (product.product_weight * quantity) * avg_cost_per_kg
        )

    def _create_analytic_line(
        self, amount, product, account_field, analytic_account, stock_move_id
    ):
        """Creates a single analytic line."""
        return self.env["account.analytic.line"].create(
            {
                "name": self.name or "",
                account_field: analytic_account.id,
                "amount": amount,
                "product_id": product.id,
                "stock_move_id": stock_move_id,
            }
        )

    def _generate_analytic_lines(self, amount, product, stock_move_id):
        """Generates analytic lines for both positive and negative accounts."""
        if self.positive_analytic_account_id:
            positive_field = (
                self.positive_analytic_account_id.root_plan_id._column_name()
            )
            if positive_field:
                self._create_analytic_line(
                    amount,
                    product,
                    positive_field,
                    self.positive_analytic_account_id,
                    stock_move_id,
                )

        if self.negative_analytic_account_id:
            negative_field = (
                self.negative_analytic_account_id.root_plan_id._column_name()
            )
            if negative_field:
                self._create_analytic_line(
                    -amount,
                    product,
                    negative_field,
                    self.negative_analytic_account_id,
                    stock_move_id,
                )

    @api.model
    def generate_analytic_lines(self, stock_move):
        """Generates analytic lines based on matching stock analytic models."""

        product = stock_move.product_id
        quantity = stock_move.product_uom_qty
        location_from_id = stock_move.location_id.id
        location_dest_id = stock_move.location_dest_id.id

        if product.product_weight <= 0:
            # If there is no weight, we cannot calculate the cost.
            raise ValidationError(_("The product weight must be greater than zero."))

        records = self.search([])

        for record in records:
            if record._is_match(
                location_from_id, location_dest_id, product.categ_id.id
            ):
                # If the stock moves matches with the model criteria,
                # then generate the analytic lines.
                amount = self._compute_amount(product, quantity, record.avg_cost_per_kg)
                record._generate_analytic_lines(amount, product, stock_move.id)
                break
