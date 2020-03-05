 
# -*- coding: utf-8 -*-
{
    'name': "shared_inventory",

    'summary': """
        In Odoo, there are 4 different products with the same SKU, but I can buy and sell any part number, 
        and all inventory values of each part number should increase/decrease by the same amount.
    """,

    'description': """
        I have 1 product (SKU) that has 4 possible alternative Part numbers. 
        In my inventory system, they are the same part and are interchangeable, 
        however on the market place I post them online to they are separate products.

        SKU: ABC123
        P#1: 11111
        P#2: 22222
        P#3: 33333
        P#4: 44444
        
        Inventory Value of SKU ABC123 = 10 units
        
        If I sell 1 unit P#2 my inventory value of ABC123 should decrease to 9 units.
        If I sell 5 units of P#4 my inventory value of ABC123 should decrease to 4 units.
        If I buy 15 units of P#3 my inventory value of ABC123 should increase to 19 units.
        
        In Odoo, they are 4 different products with the same SKU, but I can buy and sell any part number, 
        and all inventory values of each part number should increase/decrease by the same amount.
    """,

    'author': "Odoo",
    'website': "http://www.odoo.com",

    # any module necessary for this one to work correctly
    'depends': ['stock', 'account', 'sale_management', 'account_accountant', 'purchase'],

    # always loaded
    'data': [
        'views/views.xml',
        'security/ir.model.access.csv'
    ],
}