# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import base64
import csv
import logging
import time
from datetime import datetime
from io import StringIO
from tempfile import NamedTemporaryFile

from odoo import models, api, fields, _
# from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SPSCommerceSaleRequisition(models.Model):
    _name = 'sps.commerce.requisition.ept'
    _inherit = ["mail.thread"]
    _description = 'SPSCommerce Sale Requisition'
    _rec_name = 'name'

    name = fields.Char()
    instance_id = fields.Many2one('sps.commerce.instance.ept', string="Instance")
    # requisition_line_ids = fields.One2many('sps.commerce.sale.requisition.line.ept', 'requisition_id',
    #                                        string="Requisition Lines")
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


