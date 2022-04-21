from odoo import models, api, fields


class SPSCommerceSaleRequisitionLine(models.Model):
    _name = 'sps.commerce.sale.requisition.line.ept'
    _description = 'SPSCommerce Sale Requisition Line'

    requisition_id = fields.Many2one('sps.commerce.requisition.ept', ondelete="cascade")
    line_no = fields.Char()
    product_id = fields.Many2one('product.product', string='Product')
    product_uom_qty = fields.Float(string="Product Qty")
    product_ack_qty = fields.Float(string="Acknowledged Quantity")
    backorder_qty = fields.Float(string="Backorder Quantity")
    sps_line_code_type = fields.Char(string="Code type")
    sps_line_code = fields.Char(string="Line code")
    sps_line_reference = fields.Char()
    vendor_sku_reference = fields.Char()
    gtin_reference = fields.Char()
    upc_reference = fields.Char()
    unit_price = fields.Float()
    cost_price = fields.Float()
    delivery_date = fields.Date()
    max_delivery_date = fields.Date()
    order_line_note = fields.Text()
    merchandise_type_code = fields.Char()
    line_description = fields.Text()
    product_availability = fields.Selection([('IA', 'Item Accepted'),
                                             ('IB', 'Item Back ordered'),
                                             ('IP', 'Item Accepted- Price Changed'),
                                             ('IQ', 'Item Accepted- Quantity Changed'),
                                             ('IR', 'Item Rejected')],
                                            string="Product Availability", default='IA')
    free_qty = fields.Float(compute='_compute_product_free_qty')

    @api.depends('product_id.free_qty')
    def _compute_product_free_qty(self):
        for record in self:
            record.free_qty = record.product_id and record.product_id.with_context(
                warehouse_id=record.requisition_id.instance_id.warehouse_id.ids).free_qty
