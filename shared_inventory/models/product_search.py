# -*- coding: utf-8 -*-

import collections
from . import helpers
from collections import defaultdict, MutableMapping, OrderedDict

from odoo import api, models, fields

export_helper = helpers.export_helper
find_expression = helpers.find_expression
insert_expression = helpers.insert_expression

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _export_rows(self, fields, *, _is_toplevel_call=True):
        quants = export_helper(self=self, fields=fields, BaseModel=models.BaseModel, collections=collections, _is_toplevel_call=_is_toplevel_call)
        return quants

class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _export_rows(self, fields, *, _is_toplevel_call=True):
        quants = export_helper(self=self, fields=fields, BaseModel=models.BaseModel, collections=collections, _is_toplevel_call=_is_toplevel_call)
        return quants

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        
        if args is None:
            args = []

        found = find_expression('product_id', args)
        check = find_expression('product_id.internal_ref_ids.name', args)

        if found['level'] > -1 and check['level'] < 0:
            args = insert_expression(args, found['level'], found['index'], '|', ['product_id.internal_ref_ids.name', 'ilike', found['value'][2]])

        return super(StockMoveLine, self)._search(args=args, offset=offset, order=order, count=count, access_rights_uid=access_rights_uid)
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        
        if args is None:
            args = []
        
        found = find_expression('product_id', args)
        check = find_expression('product_id.internal_ref_ids.name', args)

        if found['level'] > -1 and check['level'] < 0:
            args = insert_expression(args, found['level'], found['index'], '|', ['product_id.internal_ref_ids.name', 'ilike', name])

        return super(StockMoveLine, self)._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)

    @api.model
    def _export_rows(self, fields, *, _is_toplevel_call=True):
        lines = export_helper(self=self, fields=fields, BaseModel=models.BaseModel, collections=collections, _is_toplevel_call=_is_toplevel_call)
        return lines

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    internal_ref_ids = fields.Many2many(string='Other Reference Numbers', comodel_name='product.alias', relation='shared_inventory_product_alias')
    
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        
        if args is None:
            args = []
        found = find_expression('default_code', args)

        if found['level'] > -1:
            args = insert_expression(args, found['level'], found['index'], '|', ['internal_ref_ids.name', 'ilike', found['value'][2]])

        return super(ProductTemplate, self)._search(args=args, offset=offset, order=order, count=count, access_rights_uid=access_rights_uid)
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        
        if args is None:
            args = []
        found = find_expression('default_code', args)

        if found['level'] > -1:
            args = insert_expression(args, found['level'], found['index'], '|', ['internal_ref_ids.name', 'ilike', name])

        return super(ProductTemplate, self)._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    internal_ref_ids = fields.Many2many(string='Other Reference Numbers', comodel_name='product.alias', related='product_tmpl_id.internal_ref_ids')
    
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        
        if args is None:
            args = []
        found = find_expression('default_code', args)

        if found['level'] > -1:
            args = insert_expression(args, found['level'], found['index'], '|', ['internal_ref_ids.name', 'ilike', found['value'][2]])

        return super(ProductProduct, self)._search(args=args, offset=offset, order=order, count=count, access_rights_uid=access_rights_uid)
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        
        if args is None:
            args = []
        found = find_expression('default_code', args)

        if found['level'] > -1:
            args = insert_expression(args, found['level'], found['index'], '|', ['internal_ref_ids.name', 'ilike', name])

        return super(ProductProduct, self)._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)