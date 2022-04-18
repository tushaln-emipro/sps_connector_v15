# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class SPSCommerceProduct(models.Model):
    """
    This model is store SPSCommerce and odoo_sku with vendor id
    """
    _name = 'sps.commerce.product.ept'
    _description = 'SPSCommerce Product'
    _rec_name = 'sps_commerce_sku'

    sps_commerce_sku = fields.Char(string='SPSCommerce SKU', help='SPSCommerce product SKU')
    product_id = fields.Many2one('product.product', string='Product', help='Product')
    instance_id = fields.Many2one('sps.commerce.instance.ept',
                                  string='Instance',
                                  help='SPSCommerce Instance')
    barcode = fields.Char(string="Barcode", help='Product Barcode')

    def check_sps_product_exist_or_not(self, instance, default_code, sps_commerce_sku, barcode, log_lines):
        """

        :param instance:
        :param default_code:
        :return:
        """
        product_obj = self.env['product.product']
        odoo_product = product_obj.search([('default_code', '=', default_code)], limit=1)
        if not odoo_product:
            log_val = {
                'default_code': default_code,
                'message': 'Odoo Product not found %s' % default_code,
            }
            log_lines.append([0, 0, log_val])
        else:
            sps_commerce_product = self.search(
                [('sps_commerce_sku', '=', sps_commerce_sku),
                 ('instance_id', '=', instance.id or False)])
            if not sps_commerce_product:
                values = {'instance_id': instance.id,
                          'product_id': odoo_product.id,
                          'sps_commerce_sku': sps_commerce_sku,
                          'barcode': barcode,
                          }
                product_id = self.create(values)
                # .append(product_id.id)
            else:
                sps_commerce_product.write({'product_id': odoo_product.id})
        return log_lines
