import base64
import csv
import logging
import os
from io import StringIO

from odoo import models, fields, _
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)


class SPSCommerceImportExport(models.TransientModel):
    _name = 'sps.commerce.import.export.ept'
    _description = 'SPSCommerce Import/Export Wizard'

    instance_id = fields.Many2one('sps.commerce.instance.ept', string="Instance")
    operation_type = fields.Selection([('import_purchase_order', 'Import Purchase Orders'),
                                       ('export_shipment_notice', 'Export Shipment notice'),
                                       ('export_invoice', 'Export Invoice'),
                                       ('sync_product', 'Sync Products')])
    file = fields.Binary(string='Choose File', help='Import Product CSV File')
    file_name = fields.Char(string='Import File Name', help='Import File Name')
    delimiter = fields.Selection([('tab', 'Tab'), ('semicolon', 'Semicolon'), ('comma', 'Comma')],
                                 string="Separator", default='comma', required=True)

    def download_sample_attachment(self):
        """
            Download the Sample Attachment.
            :return: dictionary
        """
        attachment = self.env['ir.attachment'].search([('name', '=', 'import_product_sample_sps_commerce.csv')])
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'new',
            'nodestroy': False,
        }

    def execute(self):
        """
            import order from the directory
            :return: the action of product
        """
        if self.operation_type == 'sync_product':
            self.import_csv_file()
        if self.operation_type == 'import_purchase_order':
            self.env['sps.commerce.requisition.ept'].import_order_from_sps_commerce(self.instance_id)
        if self.operation_type == 'export_shipment_notice':
            picking_ids = self.env['stock.picking'].search(
                [('state', '=', 'done'), ('is_sps_commerce_picking', '=', True),
                 ('is_sps_asn_send', '=', False),
                 ('sps_instance_id', '=', self.instance_id.id)])
            requisition_ids = picking_ids.mapped('sps_requisition_id')
            if not requisition_ids:
                _logger.info("There are no Requisitions found for export shipment notice to SPSCommerce")
            for requisition in requisition_ids:
                requisition.send_advance_shipment_notice()
        if self.operation_type == 'export_invoice':
            invoice_ids = self.env['account.move'].search([('invoice_payment_state', 'in', ['open', 'paid']),
                                                           ('is_sps_commerce_invoice', '=', True),
                                                           ('is_sps_invoice_send', '=', False),
                                                           ('sps_instance_id', '=', self.instance_id.id)])
            requisition_ids = invoice_ids.mapped('sps_requisition_id')
            if not requisition_ids:
                _logger.info("There are no Requisitions found for export invoice to the SPSCommerce")
            for requisition in requisition_ids:
                requisition.send_invoice_edi_to_sps()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def import_csv_file(self):
        """
        This method is used
        :return:
        """
        if self.file and self.instance_id and self._get_file_type(self.file_name):
            sps_commerce_product_obj = self.env['sps.commerce.product.ept']
            common_log_book_obj = self.env['common.log.book.ept']
            csv_file = StringIO(base64.b64decode(self.file).decode())
            file_write = open('/tmp/products.csv', 'w+')
            file_write.writelines(csv_file.getvalue())
            file_write.close()
            log_lines = []
            if self.delimiter == "tab":
                reader = csv.DictReader(open('/tmp/products.csv', "rU"), delimiter="\t")
            elif self.delimiter == "semicolon":
                reader = csv.DictReader(open('/tmp/products.csv', "rU"), delimiter=";")
            else:
                reader = csv.DictReader(open('/tmp/products.csv', "rU"), delimiter=",")

            if reader and reader.fieldnames and len(reader.fieldnames) == 3:
                log = common_log_book_obj.create_sps_commerce_process_log('sps.commerce.product.ept', 'import',
                                                                          'Product Import '
                                                                          'Operation')
                log.write({'sps_commerce_instance_id': self.instance_id.id})
                for line in reader:
                    default_code = line.get('default_code', '')
                    sps_commerce_sku = line.get('sps_commerce_sku', '')
                    barcode = line.get('barcode', '')
                    ## set default price 1
                    log_lines = sps_commerce_product_obj.check_sps_product_exist_or_not(self.instance_id, default_code,
                                                                                        sps_commerce_sku, barcode,
                                                                                        log_lines)
                log.write({'log_lines': log_lines})
            else:
                raise Warning(_(
                    "Either file is invalid or proper delimiter/separator is not specified "
                    "or not found required fields."))
        else:
            raise Warning(_(
                "Either file format is not csv or proper delimiter/separator is not specified"))

    @staticmethod
    def _get_file_type(file_name):
        """
            This method is used to find file type using os library if file type is not .csv
            then return False
            :param file_name:file name
            :return:Boolean
            Added By: Mansi Ramani
        """
        is_csv_type = False
        file_type = os.path.splitext(file_name)
        if len(file_type) == 2 and file_type[1] == '.csv':
            is_csv_type = True
        return is_csv_type
