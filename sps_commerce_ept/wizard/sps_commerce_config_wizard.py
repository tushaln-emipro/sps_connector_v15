from odoo import models, fields
from odoo.exceptions import UserError


class SPSCommerceConfigWizard(models.TransientModel):
    _name = "spscommerce.config.wizard"
    _description = "SPSCommerce Configuration Wizard"

    name = fields.Char(string='Instance Name', help='SPSCommerce Instance Name')
    company_id = fields.Many2one('res.company', string='Company Name',
                                 help='SPSCommerce company reference.')
    sps_supplier_id = fields.Char(string="Supplier ID")
    is_production_environment = fields.Boolean()
    sftp_connection_id = fields.Many2one('ftp.server.ept', string='Connection',
                                         help='SPSCommerce instance connection reference.')

    def create_sps_commerce_instance(self):
        """
        Use: Create SPS commerce instance
        Added by: Ekta Bhut @Emipro Technologies
        Added on: 30/11/20
        :return: None
        """
        instance_obj = self.env['sps.commerce.instance.ept']
        is_instance_already_exist = instance_obj.search([('sps_supplier_id', '=', self.sps_supplier_id)])
        if is_instance_already_exist:
            raise UserError("SPSCommerce Instance is already exist with this Credentials")
        values = {
            'name': self.name,
            'company_id': self.company_id.id,
            'sps_supplier_id': self.sps_supplier_id,
            'is_production_environment': self.is_production_environment
        }
        if self.is_production_environment:
            values.update({'sftp_connection_id': self.sftp_connection_id.id, })
        else:
            values.update({'test_sftp_connection_id': self.sftp_connection_id.id, })

        instance_obj.create(values)
        return {'type': 'ir.actions.client', 'tag': 'reload'}
