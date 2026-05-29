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
