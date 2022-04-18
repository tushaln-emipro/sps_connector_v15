from odoo import models, fields


class FTPServer(models.Model):
    _inherit = 'ftp.server.ept'

    default_sps_upload_dir_id = fields.Many2one('ftp.directory.ept', string='Default Upload Path')
    default_sps_receive_dir_id = fields.Many2one('ftp.directory.ept', string='Default Download Path')
