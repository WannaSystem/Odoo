from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

class WebsiteSale(WebsiteSale):
    def _get_search_domain(self, search, category, attrib_values, search_in_description=True):
        print(search)
        return super(WebsiteSale, self)._get_search_domain(search, category, attrib_values, search_in_description)