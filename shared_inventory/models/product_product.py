# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.tools.float_utils import float_round

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _compute_quantities_dict(self, lot_id=False, owner_id=False, package_id=False, from_date=False, to_date=False):
        total_qty = {}
        for temp in self:
            sku = temp.sku_id if temp.sku_id else temp

            counts = sku._compute_product_quantities(lot_id, owner_id, package_id, from_date, to_date)
            total_qty[temp.id] = {
                'incoming_qty': counts[sku.id]['incoming_qty'],
                'outgoing_qty': counts[sku.id]['outgoing_qty'],
                'qty_available': counts[sku.id]['qty_available'],
                'virtual_available': counts[sku.id]['virtual_available']
            }

            for p in sku.sub_product_ids:
                counts = p._compute_product_quantities(lot_id, owner_id, package_id, from_date, to_date)
                total_qty[temp.id]['incoming_qty'] += counts[p.id]['incoming_qty']
                total_qty[temp.id]['outgoing_qty'] += counts[p.id]['outgoing_qty']
                total_qty[temp.id]['qty_available'] += counts[p.id]['qty_available']
                total_qty[temp.id]['virtual_available'] += counts[p.id]['virtual_available']

        return total_qty