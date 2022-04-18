# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api


class ResConfig(models.TransientModel):
    _inherit = "res.config.settings"

    sps_commerce_instance_id = fields.Many2one('sps.commerce.instance.ept', string="SPSCommerce Instance")
    sps_supplier_id = fields.Char(string="Supplier ID", help="SPSCommerce Supplier ID")
    sps_commerce_company_id = fields.Many2one('res.company', string='SPSCommerce Company',
                                              help='SPSCommerce Default company')

    # Sales Related
    sps_commerce_warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                                help='Stock warehouse reference.')
    sps_commerce_global_channel_id = fields.Many2one('global.channel.ept', string='Global Channel',
                                                     help='Global channel reference.')
    sps_commerce_sales_channel_id = fields.Many2one('crm.team', string='Sales Channel', help='Sales channel reference.')
    sps_commerce_pricelist_id = fields.Many2one('product.pricelist', string='Pricelist',
                                                help='Default sale order pricelist.')
    is_auto_confirm_requisition = fields.Boolean(default=False)

    # Connection Related
    sps_commerce_sftp_connection_id = fields.Many2one('ftp.server.ept', string='SFTP Connection',
                                                      help='SFTP connection')
    sps_commerce_test_sftp_connection_id = fields.Many2one('ftp.server.ept', string='Test SFTP Connection',
                                                           help='SFTP connection')

    # Account Related
    sps_commerce_payment_term_id = fields.Many2one('account.payment.term', string='Payment Term',
                                                   help='Sale order payment term.')

    sps_commerce_workflow_id = fields.Many2one('sale.workflow.process.ept', string='Auto Workflow Process',
                                               help='Auto Workflow process id')
    sps_commerce_carrier_id = fields.Many2one('delivery.carrier', string='Delivery Carrier',
                                              help='If order has not any delivery carrier then this carrier will be used.')
    spscommerce_qualifier = fields.Char(string='SPSCommerce Qualifier',
                                        help='SPSCommerce Qualifier which is provided by SPSCommerce. Maximum 2 Characters.')
    sps_commerce_vendor_qualifier = fields.Char(string='Vendor Qualifier',
                                                help='Vendor Qualifier which is provided by SPSCommerce. Maximum 2 Characters.')
    sps_commerce_production_environment = fields.Boolean(string='Connection Type',
                                                         help='Connection type for communication purpose. '
                                                              'If testing environment then data will treat as test data.')
    sps_remit_partner_id = fields.Many2one('res.partner', string='Remit Partner',
                                           help='This partner address is used as Remittance Partner to send an invoice '
                                                'to the SPSCommerce.')

    @api.onchange('sps_commerce_instance_id')
    def onchange_sps_commerce_instance_id(self):
        instance = self.sps_commerce_instance_id or False
        values = {}
        if instance:
            values.update({  # 'sps_commerce_company_id': instance.company_id and instance.company_id.id or False,
                'sps_supplier_id': instance.sps_supplier_id or False,
                'sps_commerce_warehouse_id': instance.warehouse_id and instance.warehouse_id.id or False,
                'sps_commerce_global_channel_id': instance.global_channel_id and
                                                  instance.global_channel_id.id or False,
                'sps_commerce_sales_channel_id': instance.sales_channel_id and
                                                 instance.sales_channel_id.id or False,
                'sps_commerce_pricelist_id': instance.pricelist_id and instance.pricelist_id.id or False,
                'sps_commerce_sftp_connection_id': instance.sftp_connection_id and
                                                   instance.sftp_connection_id.id or False,
                'sps_commerce_test_sftp_connection_id': instance.test_sftp_connection_id and
                                                        instance.test_sftp_connection_id.id or False,
                'sps_commerce_payment_term_id': instance.payment_term_id and instance.payment_term_id.id
                                                or False,
                'sps_commerce_workflow_id': instance.workflow_id and instance.workflow_id.id or False,
                'sps_commerce_carrier_id': instance.carrier_id and instance.carrier_id.id or False,
                'spscommerce_qualifier': instance.spscommerce_qualifier or False,
                'sps_commerce_vendor_qualifier': instance.vendor_qualifier or False,
                'sps_remit_partner_id': instance.remit_partner_id and instance.remit_partner_id.id or
                                        False,
                'is_auto_confirm_requisition': instance.is_auto_confirm_requisition
            })
            self.update(values)

    def execute(self):
        """
        This method is used to save SPSCommerce Instance configuration.
        :return:
        """
        values = {}
        if self.sps_commerce_instance_id:
            # values['company_id'] = self.sps_commerce_company_id and self.sps_commerce_company_id.id
            values['warehouse_id'] = self.sps_commerce_warehouse_id and self.sps_commerce_warehouse_id.id or False
            values['payment_term_id'] = self.sps_commerce_payment_term_id and self.sps_commerce_payment_term_id.id or \
                                        False
            values['sftp_connection_id'] = self.sps_commerce_sftp_connection_id and \
                                           self.sps_commerce_sftp_connection_id.id or \
                                           False
            values['test_sftp_connection_id'] = self.sps_commerce_test_sftp_connection_id and \
                                                self.sps_commerce_test_sftp_connection_id.id or False
            values['global_channel_id'] = self.sps_commerce_global_channel_id and self.sps_commerce_global_channel_id.id \
                                          or False
            values['pricelist_id'] = self.sps_commerce_pricelist_id and self.sps_commerce_pricelist_id.id or False
            values['sales_channel_id'] = self.sps_commerce_sales_channel_id and self.sps_commerce_sales_channel_id.id or \
                                         False
            values['workflow_id'] = self.sps_commerce_workflow_id and self.sps_commerce_workflow_id.id or False
            values['carrier_id'] = self.sps_commerce_carrier_id and self.sps_commerce_carrier_id.id or False
            # values['is_production_environment'] = self.sps_commerce_production_environment
            values['spscommerce_qualifier'] = self.spscommerce_qualifier
            values['vendor_qualifier'] = self.sps_commerce_vendor_qualifier
            values['remit_partner_id'] = self.sps_remit_partner_id and self.sps_remit_partner_id.id or False
            values['is_auto_confirm_requisition'] = self.is_auto_confirm_requisition
            self.sps_commerce_instance_id.write(values)
        return super(ResConfig, self).execute()
