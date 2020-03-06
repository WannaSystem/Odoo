# -*- coding: utf-8 -*-
from odoo import api, models, fields

def find_expression(key=None, array=[]):
    result = { 'level': -1, 'index': -1, 'value': None }
    if key is None: 
        return result

    n = -1
    count = -1
    for a in array:
        if '&' in a or '|' in a:
            n = -1
            count += 1
        if key in a:
            if count < 0: 
                count += 1
            result['level'] = count
            result['index'] = n+1
            result['value'] = a
            return result
        else: 
            n += 1

    return result

def insert_expression(array=[], level=0, after=0, operator='|', expr=None):
    
    n = -1
    count = -1
    tree = []

    for a in array:
        if count == level and n == after: 
            tree.insert(count-n, [operator])
            
            count += 1
            tree[count].insert(n+1, expr)
            
            n += 2
            tree[count].append(a)
        elif '&' in a or '|' in a:
            n = -1
            count += 1
            tree.append([a])
        else: 
            n += 1
            if count < 0: 
                count += 1
                tree.append([])
            tree[count].append(a)

    result = []
    for t in tree:
        for e in t:
            result.append(e)
    
    return result


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

        return super(ProductTemplate, self)._name_search(
            name=name, args=args,
            operator=operator, limit=limit, name_get_uid=name_get_uid)

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

        return super(ProductProduct, self)._name_search(
            name=name, args=args,
            operator=operator, limit=limit, name_get_uid=name_get_uid)