# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
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
