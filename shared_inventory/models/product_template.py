# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.tools.float_utils import float_round

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sku_id = fields.Many2one(string='SKU', comodel_name='product.template', ondelete='cascade')
    sub_product_ids = fields.One2many(string='Sub-products', comodel_name='product.template', inverse_name='sku_id', ondelete='cascade')

    def _compute_quantities_dict(self):
        # TDE FIXME: why not using directly the function fields ?
        variants_available = self.mapped('product_variant_ids')._product_available()
        prod_available = {}
        for template in self:
            qty_available = 0
            virtual_available = 0
            incoming_qty = 0
            outgoing_qty = 0

            if template.sku_id:
                qty_available = template.sku_id["qty_available"]
                virtual_available = template.sku_id["virtual_available"]
                incoming_qty = template.sku_id["incoming_qty"]
                outgoing_qty = template.sku_id["outgoing_qty"]

            for p in template.product_variant_ids:
                qty_available += variants_available[p.id]["qty_available"]
                virtual_available += variants_available[p.id]["virtual_available"]
                incoming_qty += variants_available[p.id]["incoming_qty"]
                outgoing_qty += variants_available[p.id]["outgoing_qty"]

            for p in template.sub_product_ids:
                qty_available += p["qty_available"]
                virtual_available += p["virtual_available"]
                incoming_qty += p["incoming_qty"]
                outgoing_qty += p["outgoing_qty"]
            
            prod_available[template.id] = {
                "qty_available": qty_available,
                "virtual_available": virtual_available,
                "incoming_qty": incoming_qty,
                "outgoing_qty": outgoing_qty,
            }
        return prod_available