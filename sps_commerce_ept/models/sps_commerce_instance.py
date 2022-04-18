# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
# import logging

from odoo import models, fields, api
# from odoo.addons.ftp_connector_ept.models.sftp_interface import sftp_interface

# _logger = logging.getLogger(__name__)


class SPSCommerceInstance(models.Model):
    _name = "sps.commerce.instance.ept"
    _description = "SPSCommerce Instance"

    @api.model
    def _get_default_warehouse(self):
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)],
                                                       limit=1, order='id')
        return warehouse.id if warehouse else False

    # Instance Basic Fields
    name = fields.Char(string='Instance Name', help='SPSCommerce Instance name.')
    sps_supplier_id = fields.Char(string="Supplier ID")
    company_id = fields.Many2one('res.company', string='Company', help='Default company reference.')

    # Sales Related
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', help='Stock warehouse reference.',
                                   default=_get_default_warehouse)

    global_channel_id = fields.Many2one('global.channel.ept', string='Global Channel',
                                        help='Global channel reference.')
    sales_channel_id = fields.Many2one('crm.team', string='Sales Channel', help='Sales channel reference.')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', help='Default sale order pricelist.')

    # Connection Related
    sftp_connection_id = fields.Many2one('ftp.server.ept', string='SFTP Connection',
                                         help='SFTP connection')
    test_sftp_connection_id = fields.Many2one('ftp.server.ept', string='Test SFTP Connection',
                                              help='SFTP connection')

    is_auto_confirm_requisition = fields.Boolean(default=False)
    # Account Related
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Term', help='Sale order payment term.')

    workflow_id = fields.Many2one('sale.workflow.process.ept', string='Auto Workflow Process',
                                  help='Auto Workflow process id')
    carrier_id = fields.Many2one('delivery.carrier', string='Delivery Carrier',
                                 help='If order has not any delivery carrier then this carrier will be used.')
    spscommerce_qualifier = fields.Char(string='SPSCommerce Qualifier',
                                        help='SPSCommerce Qualifier which is provided by SPSCommerce. Maximum 2 Characters.')
    vendor_qualifier = fields.Char(string='Vendor Qualifier',
                                   help='Vendor Qualifier which is provided by SPSCommerce. Maximum 2 Characters.')
    is_production_environment = fields.Boolean(string='Connection Type',
                                               help='Connection type for communication purpose. '
                                                    'If testing environment then data will treat as test data.')
    weight_uom_id = fields.Many2one('uom.uom', string="Weight",
                                    default=lambda self: self.env.ref('uom.product_uom_lb'),
                                    help="Weight Unit of Measure, select pound because the "
                                         "freight view accept the weight as pound")
    remit_partner_id = fields.Many2one('res.partner', string='Remit Partner',
                                       help='This partner address is used as Remittance Partner to send an invoice '
                                            'to the SPSCommerce.')
    active = fields.Boolean(default=True)
