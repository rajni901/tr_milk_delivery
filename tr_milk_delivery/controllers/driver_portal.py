from odoo import fields, http
from odoo.http import request


class MilkDriverPortal(http.Controller):

    @http.route('/milk/driver/<string:token>', type='http', auth='public',
                website=True, sitemap=False)
    def driver_portal(self, token, **kwargs):
        route = request.env['tr.milk.route'].sudo().search(
            [('access_token', '=', token)], limit=1)
        if not route:
            return request.render('tr_milk_delivery.driver_portal_invalid')

        today = fields.Date.today()
        sheet = request.env['tr.milk.delivery.sheet'].sudo().search([
            ('route_id', '=', route.id),
            ('delivery_date', '=', today),
        ], limit=1)

        deliveries = sheet.delivery_ids.sorted('sequence') if sheet else \
            request.env['tr.milk.delivery'].sudo()

        delivered = len(deliveries.filtered(lambda d: d.state == 'delivered'))
        total = len(deliveries)

        return request.render('tr_milk_delivery.driver_portal_template', {
            'route': route,
            'sheet': sheet,
            'deliveries': deliveries,
            'today': today,
            'token': token,
            'delivered': delivered,
            'total': total,
        })

    @http.route('/milk/driver/<string:token>/action', type='http',
                auth='public', methods=['POST'], csrf=False, website=True)
    def driver_action(self, token, delivery_id=None, action=None, **kwargs):
        route = request.env['tr.milk.route'].sudo().search(
            [('access_token', '=', token)], limit=1)
        if not route or not delivery_id:
            return request.redirect(f'/milk/driver/{token}')

        delivery = request.env['tr.milk.delivery'].sudo().browse(int(delivery_id))
        if delivery.route_id.id != route.id:
            return request.redirect(f'/milk/driver/{token}')

        if action == 'deliver':
            delivery.action_deliver()
        elif action == 'skip':
            delivery.action_skip()
        elif action == 'absent':
            delivery.action_absent()
        elif action == 'reset':
            delivery.action_reset()

        return request.redirect(f'/milk/driver/{token}')
