# -*- coding: utf-8 -*-
from odoo import api, models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    internal_ref_ids = fields.Many2many(string='Other Reference Numbers', comodel_name='product.alias', relation='shared_inventory_product_alias')

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        return super(ProductTemplate, self)._name_search(
            name=name, args=[('internal_ref_ids.name', 'in', name)],
            operator=operator, limit=limit, name_get_uid=name_get_uid)