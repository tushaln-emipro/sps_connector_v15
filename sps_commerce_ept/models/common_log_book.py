import base64
from odoo import models, fields


class CommonLogBook(models.Model):
    _inherit = 'common.log.book.ept'

    module = fields.Selection(selection_add=[('sps_commerce_ept', 'SPSCommerce Connector')])
    sps_commerce_instance_id = fields.Many2one('sps.commerce.instance.ept', string="SPSCommerce Instance")

    def create_sps_commerce_process_log(self, model_name, type, message):
        """
        This method is used to create log
        :param model_name: model_name like 'product.product'
        :param type: import operation or export operation
        :param message: message
        :return: log record
        """
        model = self.env['ir.model'].search([('model', '=', model_name)])
        vals = {
            'type': type,
            'module': 'sps_commerce_ept',
            'message': message,
            'model_id': model.id,
        }
        return self.create(vals)

    def create_attachment_of_sps_edi(self, job_id, file_name, file, message):
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
            'res_model': 'common.log.book.ept',
            'type': 'binary',
            'res_id': job_id.id,
        }
        attachment = self.env['ir.attachment'].create(vals)
        job_id.message_post(body='<b>' + '%s' % message + '</b>',
                            attachment_ids=attachment.ids)
        return attachment
