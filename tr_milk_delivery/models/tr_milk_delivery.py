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
        required=True, ondelete='restrict')

    partner_id = fields.Many2one(
        related='subscription_id.partner_id',
        string='Customer', store=True)
    product_id = fields.Many2one(
        related='subscription_id.product_id',
        string='Product', store=True)
    route_id = fields.Many2one(
        related='subscription_id.route_id',
        string='Route', store=True)
    driver_id = fields.Many2one(
        related='subscription_id.driver_id',
        string='Driver', store=True)

    delivery_date = fields.Date(
        string='Date', required=True, default=fields.Date.today)
    qty = fields.Float(
        string='Qty', required=True,
        related='subscription_id.qty', store=True, readonly=False)
    price_unit = fields.Float(
        string='Unit Price',
        related='subscription_id.price_unit', store=True, readonly=False)
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
                'delivery_date': delivery_date,
                'qty': sub.qty,
                'price_unit': sub.price_unit,
                'state': 'pending',
            }
            if sheet_id:
                vals['sheet_id'] = sheet_id
            created |= self.create(vals)
        return created
