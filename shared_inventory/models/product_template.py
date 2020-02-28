# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.tools.float_utils import float_round

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sku_id = fields.Many2one(string='SKU', comodel_name='product.template', ondelete='cascade')
    sub_product_ids = fields.One2many(string='Sub-products', comodel_name='product.template', inverse_name='sku_id', ondelete='cascade')

    on_hand = fields.Float(string='On hand', compute='_compute_on_hand')

    @api.depends('qty_available')
    def _compute_on_hand(self):
        for s in self:
            s['on_hand'] = s['qty_available']

    def _compute_quantities_dict(self, lot_id=False, owner_id=False, package_id=False, from_date=False, to_date=False):

        variants_available = self.mapped('product_variant_ids')._product_available()
        prod_available = {}
        for template in self:
            qty_available = 0
            virtual_available = 0
            incoming_qty = 0
            outgoing_qty = 0

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
        
        # for p in prod_available:
        #     print(p, prod_available[p])
        # print()

        domain_quant = []
        domain_move_in = []
        domain_move_out = []
        dates_in_the_past = False
        if lot_id is not None:
            domain_quant += [('lot_id', '=', lot_id)]
        if owner_id is not None:
            domain_quant += [('owner_id', '=', owner_id)]
            domain_move_in += [('restrict_partner_id', '=', owner_id)]
            domain_move_out += [('restrict_partner_id', '=', owner_id)]
        if package_id is not None:
            domain_quant += [('package_id', '=', package_id)]
        if dates_in_the_past:
            domain_move_in_done = list(domain_move_in)
            domain_move_out_done = list(domain_move_out)
        if from_date:
            domain_move_in += [('date', '>=', from_date)]
            domain_move_out += [('date', '>=', from_date)]
        if to_date:
            domain_move_in += [('date', '<=', to_date)]
            domain_move_out += [('date', '<=', to_date)]

        Move = self.env['stock.move']
        Quant = self.env['stock.quant']
        domain_move_in_todo = [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available'))] + domain_move_in
        domain_move_out_todo = [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available'))] + domain_move_out
        moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in_todo, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
        moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out_todo, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
        quants_res = dict((item['product_id'][0], item['quantity']) for item in Quant.read_group(domain_quant, ['product_id', 'quantity'], ['product_id'], orderby='id'))
        if dates_in_the_past:
            # Calculate the moves that were done before now to calculate back in time (as most questions will be recent ones)
            domain_move_in_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_in_done
            domain_move_out_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_out_done
            moves_in_res_past = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in_done, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
            moves_out_res_past = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out_done, ['product_id', 'product_qty'], ['product_id'], orderby='id'))

        for product in self.with_context(prefetch_fields=False):
            product_id = product.id
            rounding = product.uom_id.rounding
            if not (product_id in prod_available):
                prod_available[product_id] = {
                    'qty_available': 0.0,
                    'incoming_qty': 0.0,
                    'outgoing_qty': 0.0,
                    'virtual_available': 0.0
                }
            if dates_in_the_past:
                qty_available = quants_res.get(product_id, 0.0) - moves_in_res_past.get(product_id, 0.0) + moves_out_res_past.get(product_id, 0.0)
            else:
                qty_available = quants_res.get(product_id, 0.0)
            prod_available[product_id]['qty_available'] += float_round(qty_available, precision_rounding=rounding)
            prod_available[product_id]['incoming_qty'] += float_round(moves_in_res.get(product_id, 0.0), precision_rounding=rounding)
            prod_available[product_id]['outgoing_qty'] += float_round(moves_out_res.get(product_id, 0.0), precision_rounding=rounding)
            prod_available[product_id]['virtual_available'] += float_round(
                qty_available + prod_available[product_id]['incoming_qty'] - prod_available[product_id]['outgoing_qty'],
                precision_rounding=rounding)

        # for p in prod_available:
        #     print(p, prod_available[p])
        # print()

        for p in self:
            if not (p.id in prod_available):
                prod_available[p.id] = {
                    'qty_available': 0.0,
                    'incoming_qty': 0.0,
                    'outgoing_qty': 0.0,
                    'virtual_available': 0.0
                }
            if p.sku_id and p.sku_id.id in prod_available:
                prod_available[p.id]['qty_available'] += prod_available[p.sku_id.id]['qty_available']
                prod_available[p.id]['virtual_available'] += prod_available[p.sku_id.id]["virtual_available"]
                prod_available[p.id]['incoming_qty'] += prod_available[p.sku_id.id]["incoming_qty"]
                prod_available[p.id]['outgoing_qty'] += prod_available[p.sku_id.id]["outgoing_qty"]
            elif p.sku_id:
                prod_available[p.id]['qty_available'] += p.sku_id['qty_available']
                prod_available[p.id]['virtual_available'] += p.sku_id["virtual_available"]
                prod_available[p.id]['incoming_qty'] += p.sku_id["incoming_qty"]
                prod_available[p.id]['outgoing_qty'] += p.sku_id["outgoing_qty"]

        for s in self:
            for p in s.sub_product_ids:
                if p.id in prod_available:
                    prod_available[s.id]['qty_available'] += prod_available[p.id]["qty_available"]
                    prod_available[s.id]['virtual_available'] += prod_available[p.id]["virtual_available"]
                    prod_available[s.id]['incoming_qty'] += prod_available[p.id]["incoming_qty"]
                    prod_available[s.id]['outgoing_qty'] += prod_available[p.id]["outgoing_qty"]

        return prod_available