# -*- coding: utf-8 -*-
from odoo import api, models, fields

class InventoryAdjustment(models.Model):
    _inherit = 'stock.inventory'