import base64
import io
import secrets
from odoo import api, fields, models


class MilkRoute(models.Model):
    _name = 'tr.milk.route'
    _description = 'Milk Delivery Route'
    _order = 'name'

    name = fields.Char(string='Route Name', required=True)
    driver_id = fields.Many2one('res.users', string='Driver', required=True)
    active = fields.Boolean(default=True)
    note = fields.Text(string='Notes')
    access_token = fields.Char(
        string='Driver Portal Token', copy=False, readonly=True,
        help='Unique token for the driver portal URL. Share /milk/driver/<token> with the driver.')

    # Active delivery days
    mon = fields.Boolean(string='Monday', default=True)
    tue = fields.Boolean(string='Tuesday', default=True)
    wed = fields.Boolean(string='Wednesday', default=True)
    thu = fields.Boolean(string='Thursday', default=True)
    fri = fields.Boolean(string='Friday', default=True)
    sat = fields.Boolean(string='Saturday', default=True)
    sun = fields.Boolean(string='Sunday', default=False)

    subscription_ids = fields.One2many(
        'tr.milk.subscription', 'route_id', string='Subscriptions')
    subscription_count = fields.Integer(
        compute='_compute_counts', string='Subscriptions')
    active_subscription_count = fields.Integer(
        compute='_compute_counts', string='Active Subscriptions')

    @api.depends('subscription_ids', 'subscription_ids.state')
    def _compute_counts(self):
        for route in self:
            route.subscription_count = len(route.subscription_ids)
            route.active_subscription_count = len(
                route.subscription_ids.filtered(lambda s: s.state == 'active'))

    def action_generate_token(self):
        for route in self:
            route.access_token = secrets.token_urlsafe(24)

    def _get_portal_url(self):
        self.ensure_one()
        if not self.access_token:
            self.action_generate_token()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f'{base_url}/milk/driver/{self.access_token}'

    def action_send_driver_whatsapp(self):
        """Send the driver portal link to the driver via WhatsApp."""
        self.ensure_one()
        if not self.driver_id.phone and not self.driver_id.partner_id.phone:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Phone Number',
                    'message': f'Driver {self.driver_id.name} has no phone number set.',
                    'type': 'warning',
                },
            }
        phone = self.driver_id.partner_id.phone or self.driver_id.phone
        url = self._get_portal_url()
        msg = (
            f"Hello {self.driver_id.name},\n\n"
            f"Here is your Milk Delivery App link for route *{self.name}*:\n\n"
            f"{url}\n\n"
            f"Bookmark this link — it works every day. "
            f"Tap ✓ Delivered after each stop.\n\n"
            f"— {self.env.company.name}"
        )
        # Try WhatsApp service if available
        if 'tr.whatsapp.service' in self.env:
            svc = self.env['tr.whatsapp.service']
            try:
                svc._send_whatsapp(phone, msg)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Sent!',
                        'message': f'Driver link sent to {self.driver_id.name} via WhatsApp.',
                        'type': 'success',
                    },
                }
            except Exception:
                pass
        # Fallback: open WhatsApp Web
        import urllib.parse
        wa_url = f'https://wa.me/{phone.replace(" ", "").replace("+", "")}?text={urllib.parse.quote(msg)}'
        return {'type': 'ir.actions.act_url', 'url': wa_url, 'target': 'new'}

    def action_get_qr_code(self):
        """Generate and display QR code for the driver portal URL."""
        self.ensure_one()
        url = self._get_portal_url()
        try:
            import qrcode
            qr = qrcode.QRCode(box_size=6, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color='black', back_color='white')
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            qr_b64 = base64.b64encode(buf.getvalue()).decode()
            return {
                'type': 'ir.actions.act_window',
                'name': f'Driver QR Code — {self.name}',
                'res_model': 'tr.milk.route.qr.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_route_id': self.id,
                    'default_qr_image': qr_b64,
                    'default_portal_url': url,
                },
            }
        except ImportError:
            return {'type': 'ir.actions.act_url', 'url': url, 'target': 'new'}

    def action_view_driver_portal(self):
        self.ensure_one()
        if not self.access_token:
            self.action_generate_token()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': f'{base_url}/milk/driver/{self.access_token}',
            'target': 'new',
        }

    def action_view_subscriptions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Subscriptions — {self.name}',
            'res_model': 'tr.milk.subscription',
            'view_mode': 'list,form',
            'domain': [('route_id', '=', self.id)],
            'context': {'default_route_id': self.id},
        }

    def get_active_days(self):
        """Return list of weekday numbers (0=Mon) for this route."""
        day_map = {0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu',
                   4: 'fri', 5: 'sat', 6: 'sun'}
        return [d for d, field in day_map.items() if getattr(self, field)]
