# -*- coding: utf-8 -*-
{
    # App Information
    'name': 'Odoo SPSCommerce Connector',
    'version': '15.0',
    'category': 'Sales Management',
    'summary': 'Odoo SPSCommerce connector is provide functionality of import orders from SPSCommerce, '
               'Its include functionality of send acknowledgement, send shipment, send invoice.',
    'license': 'OPL-1',

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

    # Odoo store specific
    'currency': 'EUR',
    'depends': [
        'common_connector_library',
        'ftp_connector_ept',
    ],

    'images': [],

    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/import_product_attachment.xml',
        'data/sequence.xml',
        'data/ir_cron.xml',
        'views/view_sps_commerce_instance.xml',
        'views/view_sps_commerce_sale_requisition.xml',
        'views/view_sale_order.xml',
        'views/view_sps_commerce_product.xml',
        'views/view_common_log_book.xml',
        'views/view_sps_sftp_configuration.xml',
        'wizard/view_sps_commerce_import_export.xml',
        'wizard/view_res_config.xml',
        'wizard/view_sps_commerce_config_wizard.xml',

    ],

    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
