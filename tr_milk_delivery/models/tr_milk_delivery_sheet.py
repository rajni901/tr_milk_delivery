from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MilkDeliverySheet(models.Model):
    _name = 'tr.milk.delivery.sheet'
    _description = 'Milk Delivery Sheet'
    _inherit = ['mail.thread']
    _order = 'delivery_date desc, route_id'

    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    route_id = fields.Many2one(
        'tr.milk.route', string='Route', required=True, tracking=True)
    driver_id = fields.Many2one(
        related='route_id.driver_id', string='Driver', store=True)
    delivery_date = fields.Date(
        string='Delivery Date', required=True,
        default=fields.Date.today, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
    ], string='Status', default='draft', tracking=True)

    delivery_ids = fields.One2many(
        'tr.milk.delivery', 'sheet_id', string='Deliveries')
    delivery_count = fields.Integer(
        compute='_compute_stats', string='Total')
    delivered_count = fields.Integer(
        compute='_compute_stats', string='Delivered')
    skipped_count = fields.Integer(
        compute='_compute_stats', string='Skipped')

    @api.depends('route_id', 'delivery_date')
    def _compute_name(self):
        for sheet in self:
            route = sheet.route_id.name or ''
            date = sheet.delivery_date or ''
            sheet.name = f'{route} — {date}' if route and date else route or '/'

    @api.depends('delivery_ids.state')
    def _compute_stats(self):
        for sheet in self:
            lines = sheet.delivery_ids
            sheet.delivery_count = len(lines)
            sheet.delivered_count = len(lines.filtered(
                lambda d: d.state == 'delivered'))
            sheet.skipped_count = len(lines.filtered(
                lambda d: d.state in ('skipped', 'absent')))

    def action_confirm(self):
        for sheet in self:
            if sheet.state != 'draft':
                raise UserError(_('Only draft sheets can be confirmed.'))
            sheet.state = 'confirmed'

    def action_done(self):
        for sheet in self:
            if sheet.state != 'confirmed':
                raise UserError(_('Only confirmed sheets can be marked done.'))
            sheet.state = 'done'

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_print_sheet(self):
        return self.env.ref(
            'tr_milk_delivery.action_report_delivery_sheet'
        ).report_action(self)

    @api.model
    def auto_generate_today_sheets(self):
        """Called by cron: generate delivery sheets for today across all active routes."""
        today = fields.Date.today()
        weekday = today.weekday()
        day_map = {0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu',
                   4: 'fri', 5: 'sat', 6: 'sun'}
        day_field = day_map[weekday]

        routes = self.env['tr.milk.route'].search([
            ('active', '=', True),
            (day_field, '=', True),
        ])
        for route in routes:
            sheet = self.search([
                ('route_id', '=', route.id),
                ('delivery_date', '=', today),
            ], limit=1)
            if not sheet:
                sheet = self.create({
                    'route_id': route.id,
                    'delivery_date': today,
                    'state': 'draft',
                })
            self.env['tr.milk.delivery'].create_from_subscriptions(
                route.id, today, sheet.id)

    def action_mark_all_delivered(self):
        self.ensure_one()
        self.delivery_ids.filtered(
            lambda d: d.state == 'pending'
        ).write({'state': 'delivered'})
