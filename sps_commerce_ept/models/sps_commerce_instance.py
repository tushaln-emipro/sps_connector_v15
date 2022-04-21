from odoo import models, fields, api
from odoo.addons.ftp_connector_ept.models.sftp_interface import sftp_interface

_logger = logging.getLogger(__name__)


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
                                        help='SPSCommerce Qualifier which is provided by SPSCommerce.'
                                             'Maximum 2 Characters.')
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

    @api.model
    def create(self, vals):
        name = vals.get('name')
        sales_team = self.create_sales_team(name)
        global_channel = self.create_global_channel(name)
        vals.update({'sales_channel_id': sales_team.id,
                     'global_channel_id': global_channel.id})
        return super(SPSCommerceInstance, self).create(vals)

    def create_sales_team(self, name):
        """
        It creates new sales team for SPSCommerce instance.
        """
        crm_team_obj = self.env['crm.team']
        return crm_team_obj.create({'name': name, 'use_quotations': True})

    def create_global_channel(self, name):
        """
        It will create new global channel for the SPSCommerce Instance
        """
        global_channel_obj = self.env['global.channel.ept']
        return global_channel_obj.create({'name': name})

    def toggle_prod_environment_value(self):
        """
        This will switch environment between production and test connection
        """
        self.ensure_one()
        self.is_production_environment = not self.is_production_environment

    def cron_configuration_action(self):
        """
        This method used to open Cron configuration wizard from SPSCommerce Instance
        :return: Cron configuration wizard action
        """
        action = self.env.ref('sps_commerce_ept.action_wizard_sps_commerce_cron_configuration').read()[0]
        context = {'sps_commerce_instance_id': self.id}
        action['context'] = context
        return action

    @api.model
    def auto_import_sps_purchase_order(self, ctx={}):
        sale_requisition_obj = self.env['sps.commerce.requisition.ept']
        instance = False
        if ctx.get('instance_id'):
            instance = self.browse(ctx.get('instance_id'))
        if instance:
            sale_requisition_obj.import_order_from_sps_commerce(instance)

    @api.model
    def auto_export_sps_advance_shipment_notice(self, ctx={}):
        """
       This method is called from export Advance Shipment notice scheduler
       :param ctx: {'instance_id' : 1}
       :return: True
       """
        stock_picking_obj = self.env['stock.picking']
        instance = False
        if ctx.get('instance_id'):
            instance = self.browse(ctx.get('instance_id'))
        if instance:
            picking_ids = stock_picking_obj.search([('state', '=', 'done'), ('is_sps_commerce_picking', '=', True),
                                                    ('is_sps_asn_send', '=', False),
                                                    ('sps_instance_id', '=', instance.id)])
            requisition_ids = picking_ids.mapped('sps_requisition_id')
            if not requisition_ids:
                _logger.info("There are no Requisitions found for export shipment notice to SPSCommerce")
            for requisition in requisition_ids:
                requisition.with_context(from_cron=True).send_advance_shipment_notice()
        return True

    @api.model
    def auto_export_sps_invoice(self, ctx={}):
        """
        This method is called from Export invoice scheduler
        :param ctx: {'instance_id' : 1}
        :return: True
        """
        account_move_obj = self.env['account.move']
        instance = False
        if ctx.get('instance_id'):
            instance = self.browse(ctx.get('instance_id'))
        if instance:
            invoice_ids = account_move_obj.search([('invoice_payment_state', 'in', ['open', 'paid']),
                                                   ('is_sps_commerce_invoice', '=', True),
                                                   ('is_sps_invoice_send', '=', False),
                                                   ('sps_instance_id', '=', instance.id)])
            requisition_ids = invoice_ids.mapped('sps_requisition_id')
            if not requisition_ids:
                _logger.info("There are no Requisitions found for export invoice to the SPSCommerce")
            for requisition in requisition_ids:
                requisition.with_context(from_cron=True).send_invoice_edi_to_sps()
        return True

    @staticmethod
    def get_edi_receive_interface(ftp_server_id, directory_id):
        """
        This function is used to receive file from SFTP
        :param ftp_server_id: sftp server id
        :param directory_id: download directory
        """
        return sftp_interface(
            ftp_server_id.ftp_host,
            ftp_server_id.ftp_username,
            ftp_server_id.ftp_password,
            None,
            ftp_server_id.ftp_port,
            download_dir=directory_id.path
        )
