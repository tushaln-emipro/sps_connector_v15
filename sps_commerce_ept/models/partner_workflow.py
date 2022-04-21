from odoo import models, fields


class PartnerWorkflow(models.Model):
    _name = 'partner.workflow.ept'
    _description = 'Partner Workflow'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', string='Partner')
    is_export_poa = fields.Boolean(string='Export POA', default=False, copy=False)
    is_export_shipment = fields.Boolean(string='Export Shipment', default=False, copy=False)
    is_export_invoice = fields.Boolean(string='Export Invoice', default=False, copy=False)

    _sql_constraints = [
        ("unique_partner", "UNIQUE(partner_id)",
         "Partner is already added for the workflow.")]
