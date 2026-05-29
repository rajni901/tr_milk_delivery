from odoo import _, api, fields, models
from odoo.exceptions import UserError


class GenerateDeliverySheet(models.TransientModel):
    _name = 'tr.milk.generate.sheet'
    _description = 'Generate Delivery Sheet'

    delivery_date = fields.Date(
        string='Delivery Date', required=True, default=fields.Date.today)
    route_ids = fields.Many2many(
        'tr.milk.route', string='Routes',
        help='Leave empty to generate for all active routes.')

    def action_generate(self):
        self.ensure_one()
        routes = self.route_ids or self.env['tr.milk.route'].search(
            [('active', '=', True)])
        if not routes:
            raise UserError(_('No active routes found.'))

        weekday = self.delivery_date.weekday()
        day_map = {0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu',
                   4: 'fri', 5: 'sat', 6: 'sun'}
        day_field = day_map[weekday]

        sheets = self.env['tr.milk.delivery.sheet']
        for route in routes:
            if not getattr(route, day_field):
                continue
            # Get or create the sheet for this route/date
            sheet = self.env['tr.milk.delivery.sheet'].search([
                ('route_id', '=', route.id),
                ('delivery_date', '=', self.delivery_date),
            ], limit=1)
            if not sheet:
                sheet = self.env['tr.milk.delivery.sheet'].create({
                    'route_id': route.id,
                    'delivery_date': self.delivery_date,
                    'state': 'draft',
                })
            # Generate delivery lines
            self.env['tr.milk.delivery'].create_from_subscriptions(
                route.id, self.delivery_date, sheet.id)
            sheets |= sheet

        if not sheets:
            raise UserError(_(
                'No deliveries to generate for the selected date and routes.'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Delivery Sheets'),
            'res_model': 'tr.milk.delivery.sheet',
            'view_mode': 'list,form',
            'domain': [('id', 'in', sheets.ids)],
        }
