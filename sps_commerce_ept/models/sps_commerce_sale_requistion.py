import logging
import base64
from odoo import models, api, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SPSCommerceSaleRequisition(models.Model):
    _name = 'sps.commerce.requisition.ept'
    _inherit = ["mail.thread"]
    _description = 'SPSCommerce Sale Requisition'
    _rec_name = 'name'

    name = fields.Char()
    instance_id = fields.Many2one('sps.commerce.instance.ept', string="Instance")
    requisition_line_ids = fields.One2many('sps.commerce.sale.requisition.line.ept', 'requisition_id',
                                           string="Requisition Lines")
    company_id = fields.Many2one('res.company', string='Company')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    state = fields.Selection([('draft', 'Draft'),
                              ('processed', 'Processed'),
                              ('ack_send', 'Ack Sent'),
                              ('asn_send', 'Asn Sent'),
                              ('done', 'Done'),
                              ('cancel', 'Cancel')], track_visibility=True, string='Order State', default='draft')
    partner_id = fields.Many2one('res.partner', string='Partner')
    partner_shipping_id = fields.Many2one('res.partner', string='Shipping Address')
    partner_invoice_id = fields.Many2one('res.partner', string="Invoice Address")
    date_order = fields.Datetime(string='Order Date')
    purchase_order_reference = fields.Char()
    vendor_number = fields.Char()
    order_note = fields.Text(string="Order Note")
    sender_id = fields.Char(string="Sender ID")
    receiver_id = fields.Char(string="Receiver ID")
    buyer_id = fields.Char(string="Buyer ID")
    buyer_address = fields.Char(string="Buyer Address")
    delivery_date = fields.Date(string="Delivery Date")
    max_delivery_date = fields.Date(string="Maximum Delivery Date")
    max_shipping_date = fields.Date(string="Maximum Shipping Date")
    invoice_party_id = fields.Char(string='Invoice Party ID')
    general_information = fields.Text()
    sale_order_id = fields.Many2one('sale.order', string='Vendor Order')
    order_count = fields.Integer(compute='_compute_order_count', string='Count')
    customer_contract_number = fields.Char()
    order_total = fields.Float(readonly=True)
    is_acknowledgement_send = fields.Boolean(string='Is Acknowledgement Send?')
    is_asn_send = fields.Boolean(default=False)
    is_invoice_send = fields.Boolean(default=False)
    sps_payment_term = fields.Char("SPS Payment term")
    sps_payment_term_reference = fields.Char()
    edi_version = fields.Char()

    def import_order_from_sps_commerce(self, instance):
        """
        This method is used to import the purchase order from the SPSCommerce.
        :param instance: SPSCommerce Instance
        :return: True
        """
        ftp_server_id = instance.sftp_connection_id if instance.is_production_environment \
            else instance.test_sftp_connection_id
        directory_id = ftp_server_id.default_sps_receive_dir_id
        if not directory_id:
            raise UserError("Default download directory is not set in SFTP configuration, Please Set it to import "
                            "purchase order")
        files_to_delete = []
        with instance.get_edi_receive_interface(ftp_server_id, directory_id) \
                as edi_interface:
            try:
                filenames_dict = edi_interface.pull_from_ftp("PO")
            except:
                raise Warning(_("Please check SFTP connection"))
        for server_filename, filename in filenames_dict.items():
            with open(filename) as file:
                do_not_delete = False
                job_id = self.create_requisition_log_ept(instance, message='Sale Requisition Log')
                requisition = self.read_sps_edi_file(instance, file, job_id, delimiter="*")
                if requisition:
                    self.create_attachment_of_edi(requisition, server_filename, file,
                                                  'SPSCommerce requisition is created')
                    if instance.is_auto_confirm_requisition and self.check_stock_for_all_requisition_lines(requisition):
                        requisition.create_sale_order()
                    files_to_delete.append(directory_id.path + '/' + server_filename)
                    job_id.res_id = requisition.id
                    _logger.info(file.name)
                else:
                    job_id.message = "Sale Requisition file can not be processed, please check the log."
                    do_not_delete = True
                    job_id.create_attachment_of_sps_edi(job_id, server_filename, file, job_id.message)
                if not job_id.log_lines and (not do_not_delete):
                    job_id.sudo().unlink()
        if files_to_delete:
            with instance.get_edi_receive_interface(ftp_server_id, directory_id) \
                    as edi_interface:
                edi_interface.delete_from_ftp(files_to_delete)
        return True

    def check_stock_for_all_requisition_lines(self, requisition):
        """
        This method will use to check stock available for all the requisition lines.
        :param requisition: SPSCommerce requisition
        :return: True or False
        """
        is_stock_available = True
        for line in requisition.requisition_line_ids:
            if line.product_uom_qty > line.free_qty:
                is_stock_available = False
                break
        return is_stock_available

    def create_attachment_of_edi(self, requistion, file_name, file, message):
        """
        This method is used to create attachment in log
        :param log: process.log object
        :param file_name: file_name
        :param message: message
        :return: True
        """
        file = open(file.name, "rb").read()
        vals = {
            'name': file_name,
            'datas': base64.b64encode(file),
            'name': file_name,
            'res_model': 'sps.commerce.requisition.ept',
            'type': 'binary',
            'res_id': requistion.id,
        }
        attachment = self.env['ir.attachment'].create(vals)
        requistion.message_post(body='<b>' + '%s' % message + '</b>', attachment_ids=attachment.ids)
        return attachment

    def read_sps_edi_file(self, instance, file, job_id, delimiter="*"):
        """
        This method is used to read SPSCommerce EDI file and based on that we will create SPSCommerce Requisition in
        Odoo.
        :param job_id: common log book record
        :param instance: SPSCommerce Instance
        :param file: File
        :param delimiter: Delimiter for the file read
        :return: Requisition
        """

        is_purchase_order_edi, order_info, message_info, order_line_info = self.process_edi_segments(instance, file,
                                                                                                     delimiter, job_id)

        if is_purchase_order_edi and (not self.check_requisition_already_exist_or_not(instance, order_info)):
            requisition = self.create_sps_commerce_sale_requisition(instance, order_info, message_info)
            if requisition:
                requisition = requisition.create_sps_requisition_lines(instance, order_line_info, job_id)
        else:
            return False
        return requisition

    def check_requisition_already_exist_or_not(self, instance, order_info):
        requisition = self.search([('instance_id', '=', instance.id),
                                   ('purchase_order_reference', '=', order_info.get('purchase_order_reference'))])
        return True if requisition else False

    def create_sps_commerce_sale_requisition(self, instance, order_info, message_info):
        """
        This method is used to create SPSCommerce sale requisition record.
        :param instance: SPSCommerce Instance
        :param order_info: Requisition details
        :param message_info: Message information
        :return:SPSCommerce Requisition record
        """
        res_partner_obj = self.env['res.partner']
        partner_id, partner_invoice_id, partner_shipping_id = res_partner_obj.prepare_sps_partners(
            order_info.get('contact_customer'), order_info.get('invoice'), order_info.get('shipping'))
        sale_requisition_vals = {'partner_id': partner_id.id,
                                 'partner_invoice_id': partner_invoice_id.id,
                                 'partner_shipping_id': partner_shipping_id.id,
                                 'instance_id': instance.id,
                                 'company_id': instance.company_id.id,
                                 'date_order': order_info.get('date_order'),
                                 'purchase_order_reference': order_info.get('purchase_order_reference'),
                                 'vendor_number': order_info.get('vendor_number'),
                                 'order_note': order_info.get('order_note'),
                                 'sender_id': message_info.get('sender_id'),
                                 'receiver_id': message_info.get('receiver_id'),
                                 'max_delivery_date': order_info.get('max_delivery_date'),
                                 'delivery_date': order_info.get('delivery_date'),
                                 'max_shipping_date': order_info.get('max_shipping_date'),
                                 'general_information': order_info.get('general_information'),
                                 'pricelist_id': instance.pricelist_id.id,
                                 'customer_contract_number': order_info.get('customer_contract_number'),
                                 'order_total': order_info.get('order_total'),
                                 'sps_payment_term': order_info.get('sps_payment_term'),
                                 'edi_version': order_info.get('edi_version')
                                 }
        return self.create(sale_requisition_vals)

    def create_requisition_log_ept(self, instance, message='', operation='import'):
        """
        Method for create process log.
        :param instance:
        :param operation:
        :param message:
        :return:
        """
        model = self.env['ir.model'].search([('model', '=', 'sps.commerce.requisition.ept')])
        vals = {
            'type': operation,
            'module': 'sps_commerce_ept',
            'message': message,
            'model_id': model.id,
            'res_id': self.id,
            'sps_commerce_instance_id': instance.id
        }
        return self.env['common.log.book.ept'].create(vals)

    def create_sale_order(self):
        """
        This is the Parent function and call different sub-functions from this function.
        This function call on clicking on "Create Sale Order" button
        :return:
        """
        order_id = False
        acknowledgement_lines = self.requisition_line_ids.filtered(
            lambda l: l.product_ack_qty > 0 and l.product_availability in ['IA', 'IB', 'IQ', 'IP'])
        if acknowledgement_lines:
            sps_product_ids = acknowledgement_lines.filtered(lambda l: not l.product_id)
            if sps_product_ids:
                raise UserError(_(
                    "Odoo product is not found for Sale requisition, Please set product manually first."))
            order_id = self.create_sale_and_back_order(acknowledgement_lines)
            self.sale_order_id = order_id.id
            self.state = 'processed'
            order_id.process_orders_and_invoices_ept()
        return order_id

    def create_sale_and_back_order(self, lines, backorder=False):
        """
        Create Sale Order from Sales Requisition data.
        :param backorder_lines:
        :param backorder: boolean
        :return: order_id sale.order()
        """
        sale_order_obj = self.env['sale.order']
        sale_order_line_obj = self.env['sale.order.line']
        sale_order_vals = {
            'partner_id': self.partner_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'date_order': self.date_order,
            'warehouse_id': self.instance_id.warehouse_id.id,
            'partner_invoice_id': self.partner_invoice_id.id,
            'pricelist_id': self.instance_id.pricelist_id.id,
            'company_id': self.instance_id.company_id.id,
            'picking_policy': self.instance_id.workflow_id and self.instance_id.workflow_id.picking_policy,
            'carrier_id': self.instance_id.carrier_id.id or False,
            'state': 'draft',
            'note': self.general_information,
            'team_id': self.instance_id.sales_channel_id.id or False,
            'client_order_ref': self.purchase_order_reference or False
        }
        order_vals = sale_order_obj.create_sales_order_vals_ept(sale_order_vals)
        order_vals.update(
            {
                'sps_requisition_id': self.id,
                'sps_instance_id': self.instance_id.id,
                'auto_workflow_process_id': self.instance_id.workflow_id.id,
                'is_sps_commerce_order': True,
                'note': self.general_information, })
        order_id = sale_order_obj.create(order_vals)
        for line in lines:
            so_line_vals = {
                'order_id': order_id.id,
                'product_id': line.product_id.id,
                'company_id': self.instance_id.company_id.id,
                'name': line.product_id.name,
                'order_qty': line.product_uom_qty,
                'price_unit': line.unit_price
            }
            so_line_values = sale_order_line_obj.create_sale_order_line_ept(so_line_vals)
            sale_order_line_obj.create(so_line_values)
        return order_id

    def send_advance_shipment_notice(self):
        """
        This method is used to Send Advance shipment notice to SPSCommerce
        :return: It will return true if any details mismatch
        """
        stock_picking_obj = self.env['stock.picking']
        _logger.info("Shipment process started for Requisition %s and Purchase order reference %s" % (
            self.name, self.purchase_order_reference))
        if self.sale_order_id.picking_ids.filtered(lambda l: l.is_sps_ack_send and l.state != 'done'):
            raise UserError("Please validate Delivery order first, Then you can able to send shipment notice")
        instance_id = self.instance_id
        picking = self.sale_order_id.picking_ids.filtered(lambda l: l.is_sps_ack_send and l.state == 'done' and
                                                                    not l.is_sps_asn_send)
        if not picking:
            raise UserError("It seems delivery order is not validated or shipment notice is already sent.")
        advance_shipment_notice = stock_picking_obj.prepare_shipment_notice(picking)
        if isinstance(advance_shipment_notice, bool):
            _logger.info("Advance shipment notice not able to send for requisition %s" % self.name)
            return True
        file_name = 'SH%s.txt' % self.purchase_order_reference
        file, result = self.prepare_file_for_export(advance_shipment_notice)
        self.create_attachment_of_edi(self, file_name, file, 'Advance shipment notice is exported.')
        ftp_server_id = instance_id.sftp_connection_id if instance_id.is_production_environment else \
            instance_id.test_sftp_connection_id
        directory_id = ftp_server_id.default_sps_upload_dir_id
        with instance_id.get_edi_sending_interface(ftp_server_id, directory_id) \
                as edi_interface:
            edi_interface.push_to_ftp(file_name, file.name)
        self.write({'is_asn_send': True, 'state': 'asn_send'})
        picking.is_sps_asn_send = True

    def send_invoice_edi_to_sps(self):
        """
        This method is used to Send Invoice EDI to SPSCommerce
        """

    def sps_requisition_reset_to_draft_ept(self):
        """
        Reset sale order requisition to draft from cancelled state
        """

    def action_view_sps_order(self):
        """
        This function returns an action that displays existing orders
        of given vendor central sales order ids. It can either be an in a list or a form
        view if there is only one order to show.
        :return:action
        """
        action = self.env.ref('sale.action_quotations').read()[0]
        action['domain'] = [('id', 'in', self.sale_order_id.ids)]
        return action
