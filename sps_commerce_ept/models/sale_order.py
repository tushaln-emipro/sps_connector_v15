from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sps_instance_id = fields.Many2one('sps.commerce.instance.ept', string='SPSCommerce Instance', copy=False)
    sps_requisition_id = fields.Many2one('sps.commerce.requisition.ept', string='SPSCommerce Requisition', copy=False)
    is_sps_commerce_order = fields.Boolean(default=False, copy=False)

    def _prepare_invoice(self):
        """
        This method used set a SPSCommerce instance in customer invoice.
        @param : self
        @return: inv_val
        """
        inv_val = super(SaleOrder, self)._prepare_invoice()
        if self.sps_instance_id:
            inv_val.update({'sps_instance_id': self.sps_instance_id.id,
                            'sps_requisition_id': self.sps_requisition_id.id,
                            'is_sps_invoice_send': False})
        return inv_val
