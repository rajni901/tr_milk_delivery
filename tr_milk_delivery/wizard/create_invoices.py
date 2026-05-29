from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CreateMilkInvoices(models.TransientModel):
    _name = 'tr.milk.create.invoices'
    _description = 'Create Invoices from Deliveries'

    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True,
                          default=fields.Date.today)
    partner_ids = fields.Many2many(
        'res.partner', string='Customers',
        help='Leave empty to invoice all customers with pending deliveries.')
    route_ids = fields.Many2many(
        'tr.milk.route', string='Routes',
        help='Leave empty to include all routes.')
    invoice_date = fields.Date(
        string='Invoice Date', required=True, default=fields.Date.today)

    @api.onchange('date_to')
    def _onchange_date_to(self):
        if self.date_to and not self.date_from:
            # Default from = first day of the month
            self.date_from = self.date_to.replace(day=1)

    def action_create_invoices(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_('From Date must be before To Date.'))

        domain = [
            ('state', '=', 'delivered'),
            ('invoiced', '=', False),
            ('delivery_date', '>=', self.date_from),
            ('delivery_date', '<=', self.date_to),
        ]
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        if self.route_ids:
            domain.append(('route_id', 'in', self.route_ids.ids))

        deliveries = self.env['tr.milk.delivery'].search(domain)
        if not deliveries:
            raise UserError(_(
                'No uninvoiced delivered orders found for the selected period.'))

        # Group by customer
        partner_deliveries = {}
        for d in deliveries:
            partner_deliveries.setdefault(d.partner_id.id, self.env['tr.milk.delivery'])
            partner_deliveries[d.partner_id.id] |= d

        invoices = self.env['account.move']
        for partner_id, lines in partner_deliveries.items():
            partner = self.env['res.partner'].browse(partner_id)
            invoice_lines = []
            for d in lines:
                invoice_lines.append((0, 0, {
                    'product_id': d.product_id.id,
                    'name': f'{d.product_id.name} — {d.delivery_date}',
                    'quantity': d.qty,
                    'price_unit': d.price_unit,
                    'tax_ids': [],
                }))

            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': partner_id,
                'invoice_date': self.invoice_date,
                'invoice_line_ids': invoice_lines,
                'narration': f'Milk delivery — {self.date_from} to {self.date_to}',
            })
            lines.write({'invoiced': True, 'invoice_id': invoice.id})
            invoices |= invoice

        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices Created'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoices.ids)],
        }
