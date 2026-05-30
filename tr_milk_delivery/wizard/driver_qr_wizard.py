from odoo import fields, models


class MilkRouteQrWizard(models.TransientModel):
    _name = 'tr.milk.route.qr.wizard'
    _description = 'Driver Portal QR Code'

    route_id = fields.Many2one('tr.milk.route', string='Route')
    qr_image = fields.Binary(string='QR Code')
    portal_url = fields.Char(string='Driver Portal URL')
