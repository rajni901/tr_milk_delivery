import logging
from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MilkDelivery(models.Model):
    _name = 'tr.milk.delivery'
    _description = 'Milk Delivery Line'
    _order = 'delivery_date desc, sequence, partner_id'

    sheet_id = fields.Many2one(
        'tr.milk.delivery.sheet', string='Delivery Sheet',
        ondelete='cascade', index=True)
    subscription_id = fields.Many2one(
        'tr.milk.subscription', string='Subscription',
        ondelete='restrict')

    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True, index=True)
    product_id = fields.Many2one(
        'product.product', string='Product', required=True,
        domain=[('sale_ok', '=', True)])
    route_id = fields.Many2one('tr.milk.route', string='Route', index=True)
    driver_id = fields.Many2one('res.users', string='Driver')
    sequence = fields.Integer(string='Stop #', default=10)

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
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    wallet_deducted = fields.Boolean(string='Wallet Deducted', default=False)
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
        for delivery in self:
            delivery.write({'state': 'delivered'})
            delivery._deduct_wallet()
            delivery._send_whatsapp_notification()

    def action_skip(self):
        self.write({'state': 'skipped'})

    def action_absent(self):
        self.write({'state': 'absent'})

    def action_reset(self):
        self.write({'state': 'pending'})

    def _deduct_wallet(self):
        """Deduct delivery cost from customer wallet if available."""
        self.ensure_one()
        if self.wallet_deducted or self.subtotal <= 0:
            return
        wallet = self.env['tr.milk.wallet'].search(
            [('partner_id', '=', self.partner_id.id)], limit=1)
        if wallet and wallet.balance >= self.subtotal:
            success = wallet.deduct(
                self.subtotal,
                description=f'{self.product_id.name} — {self.delivery_date}',
                delivery_id=self.id,
            )
            if success:
                self.wallet_deducted = True
                _logger.info('Wallet deducted: partner=%s amount=%s',
                             self.partner_id.name, self.subtotal)

    def _send_whatsapp_notification(self):
        """Send WhatsApp message to customer on delivery. Requires tr_whatsapp_notifications."""
        self.ensure_one()
        if 'tr.whatsapp.service' not in self.env:
            return
        svc = self.env['tr.whatsapp.service']
        if not svc._is_enabled('tr_whatsapp.notify_invoice'):
            return
        phone = self.partner_id.phone
        if not phone:
            return
        msg = (
            f"Hello {self.partner_id.name},\n\n"
            f"Your milk delivery has been completed. 🥛\n"
            f"Product: *{self.product_id.name}*\n"
            f"Qty: *{self.qty} {self.product_id.uom_id.name}*\n"
            f"Date: *{self.delivery_date}*\n"
            f"Amount: *{self.subtotal:.2f}*\n\n"
            f"Thank you!\n— {self.env.company.name}"
        )
        try:
            svc._send_whatsapp(phone, msg)
        except Exception as e:
            _logger.warning('WhatsApp delivery notification failed: %s', e)

    @api.model
    def create_from_subscriptions(self, route_id, delivery_date, sheet_id=None):
        """Generate delivery lines from active subscriptions. Skips holidays."""
        weekday = delivery_date.weekday()
        day_map = {0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu',
                   4: 'fri', 5: 'sat', 6: 'sun'}

        subscriptions = self.env['tr.milk.subscription'].search([
            ('route_id', '=', route_id),
            ('state', '=', 'active'),
            ('start_date', '<=', delivery_date),
            '|', ('end_date', '=', False), ('end_date', '>=', delivery_date),
        ])

        Holiday = self.env['tr.milk.holiday']
        created = self.env['tr.milk.delivery']

        for sub in subscriptions:
            if weekday not in sub.get_active_days():
                continue
            existing = self.search([
                ('subscription_id', '=', sub.id),
                ('delivery_date', '=', delivery_date),
            ], limit=1)
            if existing:
                continue
            # Skip holidays
            if Holiday.is_holiday(delivery_date,
                                   partner_id=sub.partner_id.id,
                                   route_id=sub.route_id.id):
                continue

            vals = {
                'subscription_id': sub.id,
                'partner_id': sub.partner_id.id,
                'product_id': sub.product_id.id,
                'route_id': sub.route_id.id,
                'driver_id': sub.driver_id.id,
                'sequence': sub.sequence,
                'delivery_date': delivery_date,
                'qty': sub.qty,
                'price_unit': sub.price_unit,
                'state': 'pending',
            }
            if sheet_id:
                vals['sheet_id'] = sheet_id
            created |= self.create(vals)
        return created
