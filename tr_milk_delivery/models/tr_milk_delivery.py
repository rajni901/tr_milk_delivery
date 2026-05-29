from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MilkDelivery(models.Model):
    _name = 'tr.milk.delivery'
    _description = 'Milk Delivery Line'
    _order = 'delivery_date desc, partner_id'

    sheet_id = fields.Many2one(
        'tr.milk.delivery.sheet', string='Delivery Sheet',
        ondelete='cascade', index=True)
    subscription_id = fields.Many2one(
        'tr.milk.subscription', string='Subscription',
        ondelete='restrict')

    # Stored fields — auto-filled from subscription but freely editable
    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True, index=True)
    product_id = fields.Many2one(
        'product.product', string='Product', required=True,
        domain=[('sale_ok', '=', True)])
    route_id = fields.Many2one(
        'tr.milk.route', string='Route', index=True)
    driver_id = fields.Many2one('res.users', string='Driver')

    delivery_date = fields.Date(
        string='Date', required=True, default=fields.Date.today)
    qty = fields.Float(string='Qty', required=True, default=1.0)
    price_unit = fields.Float(string='Unit Price')
    subtotal = fields.Float(
        string='Subtotal', compute='_compute_subtotal', store=True)

    state = fields.Selection([
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
        ('skipped', 'Skipped'),
        ('absent', 'Customer Absent'),
    ], string='Status', default='pending', required=True, index=True)

    invoiced = fields.Boolean(string='Invoiced', default=False, index=True)
    invoice_id = fields.Many2one(
        'account.move', string='Invoice', readonly=True)
    note = fields.Char(string='Note')

    @api.depends('qty', 'price_unit')
    def _compute_subtotal(self):
        for d in self:
            d.subtotal = d.qty * d.price_unit

    @api.onchange('subscription_id')
    def _onchange_subscription_id(self):
        if self.subscription_id:
            sub = self.subscription_id
            self.partner_id = sub.partner_id
            self.product_id = sub.product_id
            self.route_id = sub.route_id
            self.driver_id = sub.driver_id
            self.qty = sub.qty
            self.price_unit = sub.price_unit

    def action_deliver(self):
        self.write({'state': 'delivered'})

    def action_skip(self):
        self.write({'state': 'skipped'})

    def action_absent(self):
        self.write({'state': 'absent'})

    def action_reset(self):
        self.write({'state': 'pending'})

    @api.model
    def create_from_subscriptions(self, route_id, delivery_date, sheet_id=None):
        """Generate delivery lines from all active subscriptions for a route/date."""
        weekday = delivery_date.weekday()  # 0=Mon
        day_map = {0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu',
                   4: 'fri', 5: 'sat', 6: 'sun'}
        day_field = day_map[weekday]

        subscriptions = self.env['tr.milk.subscription'].search([
            ('route_id', '=', route_id),
            ('state', '=', 'active'),
            ('start_date', '<=', delivery_date),
            '|', ('end_date', '=', False), ('end_date', '>=', delivery_date),
        ])

        created = self.env['tr.milk.delivery']
        for sub in subscriptions:
            active_days = sub.get_active_days()
            if weekday not in active_days:
                continue
            # Skip if already created for this date + subscription
            existing = self.search([
                ('subscription_id', '=', sub.id),
                ('delivery_date', '=', delivery_date),
            ], limit=1)
            if existing:
                continue
            vals = {
                'subscription_id': sub.id,
                'partner_id': sub.partner_id.id,
                'product_id': sub.product_id.id,
                'route_id': sub.route_id.id,
                'driver_id': sub.driver_id.id,
                'delivery_date': delivery_date,
                'qty': sub.qty,
                'price_unit': sub.price_unit,
                'state': 'pending',
            }
            if sheet_id:
                vals['sheet_id'] = sheet_id
            created |= self.create(vals)
        return created
