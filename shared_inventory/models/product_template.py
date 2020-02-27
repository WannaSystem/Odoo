# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.tools.float_utils import float_round

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sku_id = fields.Many2one(string='SKU', comodel_name='product.template', ondelete='cascade')
    sub_product_ids = fields.One2many(string='Sub-products', comodel_name='product.template', inverse_name='sku_id', ondelete='cascade')

    def _compute_on_hand(self):
        for s in self:
            return s._compute_quantities_dict[s.id]['qty_available']

    on_hand = fields.Integer(string='On hand', default=_compute_on_hand, store=True)

    def _compute_quantities_dict(self, lot_id=False, owner_id=False, package_id=False, from_date=False, to_date=False):
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

        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
        domain_quant = [('product_id', 'in', self.ids)] + domain_quant_loc
        dates_in_the_past = False
        # only to_date as to_date will correspond to qty_available
        to_date = fields.Datetime.to_datetime(to_date)
        if to_date and to_date < fields.Datetime.now():
            dates_in_the_past = True

        domain_move_in = [('product_id', 'in', self.ids)] + domain_move_in_loc
        domain_move_out = [('product_id', 'in', self.ids)] + domain_move_out_loc
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
            prod_available[product_id] = {}
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

        return prod_available