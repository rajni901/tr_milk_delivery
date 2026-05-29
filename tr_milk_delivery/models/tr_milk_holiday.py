from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MilkHoliday(models.Model):
    _name = 'tr.milk.holiday'
    _description = 'Delivery Holiday / Vacation'
    _order = 'date_from desc'

    name = fields.Char(string='Reason', required=True)
    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True)
    scope = fields.Selection([
        ('global', 'All Customers (Public Holiday)'),
        ('route', 'Specific Route'),
        ('customer', 'Specific Customer'),
    ], string='Applies To', required=True, default='global')
    route_id = fields.Many2one('tr.milk.route', string='Route')
    partner_id = fields.Many2one('res.partner', string='Customer')
    active = fields.Boolean(default=True)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for h in self:
            if h.date_from > h.date_to:
                raise ValidationError(_('From Date must be before To Date.'))

    @api.model
    def is_holiday(self, delivery_date, partner_id=None, route_id=None):
        """Return True if the given date is a holiday for the subscription."""
        domain = [
            ('date_from', '<=', delivery_date),
            ('date_to', '>=', delivery_date),
            ('active', '=', True),
        ]
        holidays = self.search(domain)
        for h in holidays:
            if h.scope == 'global':
                return True
            if h.scope == 'route' and route_id and h.route_id.id == route_id:
                return True
            if h.scope == 'customer' and partner_id and h.partner_id.id == partner_id:
                return True
        return False
