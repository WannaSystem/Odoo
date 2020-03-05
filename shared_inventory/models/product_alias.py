# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.tools.float_utils import float_round

class ProductAlias(models.Model):
    _inherit = 'product.alias'

    name = fields.Char(string='Reference Number', required=True)
    color = fields.Integer(string='Color')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Reference number already exists !"),
    ]