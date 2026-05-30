from odoo import api, fields, models


class MilkSubscription(models.Model):
    _name = 'tr.milk.subscription'
    _description = 'Milk Delivery Subscription'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'route_id, sequence, partner_id'

    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    sequence = fields.Integer(
        string='Stop #', default=10,
        help='Order in which the driver visits this customer on the route. Lower = first stop.')
    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True, tracking=True,
        domain=[('customer_rank', '>', 0)])
    product_id = fields.Many2one(
        'product.product', string='Product', required=True,
        domain=[('sale_ok', '=', True)])
    product_uom_id = fields.Many2one(
        'uom.uom', string='Unit',
        related='product_id.uom_id', readonly=True)
    qty = fields.Float(string='Qty per Delivery', default=1.0, required=True)
    price_unit = fields.Float(string='Unit Price', required=True)
    route_id = fields.Many2one(
        'tr.milk.route', string='Route', required=True, tracking=True)
    driver_id = fields.Many2one(
        related='route_id.driver_id', string='Driver', store=True)

    delivery_partner_id = fields.Many2one(
        'res.partner', string='Delivery Address',
        help='Where to deliver. Leave empty to use the customer address. '
             'Useful when customer wants delivery at a different location.')
    delivery_street = fields.Char(
        string='Street', compute='_compute_delivery_address', store=True)
    delivery_city = fields.Char(
        string='City', compute='_compute_delivery_address', store=True)
    delivery_zip = fields.Char(
        string='ZIP', compute='_compute_delivery_address', store=True)
    delivery_full = fields.Char(
        string='Full Address', compute='_compute_delivery_address', store=True)

    state = fields.Selection([
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='active', tracking=True, required=True)

    start_date = fields.Date(string='Start Date', required=True,
                             default=fields.Date.today)
    end_date = fields.Date(string='End Date')
    note = fields.Text(string='Delivery Note')

    # Delivery days — overrides route days per subscription if needed
    use_custom_days = fields.Boolean(string='Custom Delivery Days')
    mon = fields.Boolean(string='Mon')
    tue = fields.Boolean(string='Tue')
    wed = fields.Boolean(string='Wed')
    thu = fields.Boolean(string='Thu')
    fri = fields.Boolean(string='Fri')
    sat = fields.Boolean(string='Sat')
    sun = fields.Boolean(string='Sun')

    delivery_ids = fields.One2many(
        'tr.milk.delivery', 'subscription_id', string='Deliveries')
    delivery_count = fields.Integer(
        compute='_compute_delivery_count', string='Deliveries')

    @api.depends('delivery_partner_id', 'partner_id')
    def _compute_delivery_address(self):
        for sub in self:
            addr = sub.delivery_partner_id or sub.partner_id
            sub.delivery_street = addr.street or ''
            sub.delivery_city = addr.city or ''
            sub.delivery_zip = addr.zip or ''
            parts = filter(None, [addr.street, addr.city, addr.zip])
            sub.delivery_full = ', '.join(parts)

    @api.depends('partner_id', 'product_id')
    def _compute_name(self):
        for sub in self:
            partner = sub.partner_id.name or ''
            product = sub.product_id.name or ''
            sub.name = f'{partner} - {product}' if partner and product else partner or product or '/'

    @api.depends('delivery_ids')
    def _compute_delivery_count(self):
        for sub in self:
            sub.delivery_count = len(sub.delivery_ids)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id.lst_price

    @api.onchange('route_id')
    def _onchange_route_id(self):
        if self.route_id and not self.use_custom_days:
            route = self.route_id
            self.mon = route.mon
            self.tue = route.tue
            self.wed = route.wed
            self.thu = route.thu
            self.fri = route.fri
            self.sat = route.sat
            self.sun = route.sun

    def get_active_days(self):
        """Return weekday numbers (0=Mon) for this subscription's delivery days."""
        if self.use_custom_days:
            day_map = {0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu',
                       4: 'fri', 5: 'sat', 6: 'sun'}
            return [d for d, f in day_map.items() if getattr(self, f)]
        return self.route_id.get_active_days()

    def action_pause(self):
        self.write({'state': 'paused'})

    def action_activate(self):
        self.write({'state': 'active'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_view_deliveries(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Deliveries — {self.name}',
            'res_model': 'tr.milk.delivery',
            'view_mode': 'list,form',
            'domain': [('subscription_id', '=', self.id)],
        }
