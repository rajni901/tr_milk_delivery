from odoo import fields, http
from odoo.http import request


class MilkCustomerPortal(http.Controller):

    @http.route('/milk/my-deliveries', type='http', auth='user',
                website=True, sitemap=False)
    def customer_deliveries(self, **kwargs):
        partner = request.env.user.partner_id

        subscriptions = request.env['tr.milk.subscription'].sudo().search([
            ('partner_id', '=', partner.id),
        ])
        deliveries = request.env['tr.milk.delivery'].sudo().search([
            ('partner_id', '=', partner.id),
        ], order='delivery_date desc', limit=30)
        wallet = request.env['tr.milk.wallet'].sudo().search([
            ('partner_id', '=', partner.id),
        ], limit=1)

        return request.render('tr_milk_delivery.customer_portal_template', {
            'subscriptions': subscriptions,
            'deliveries': deliveries,
            'wallet': wallet,
            'partner': partner,
        })

    @http.route('/milk/my-deliveries/subscription/<int:sub_id>/<string:action>',
                type='http', auth='user', methods=['POST'],
                csrf=False, website=True)
    def customer_subscription_action(self, sub_id, action, **kwargs):
        partner = request.env.user.partner_id
        sub = request.env['tr.milk.subscription'].sudo().browse(sub_id)
        if sub.partner_id.id != partner.id:
            return request.redirect('/milk/my-deliveries')

        if action == 'pause' and sub.state == 'active':
            sub.action_pause()
        elif action == 'activate' and sub.state == 'paused':
            sub.action_activate()

        return request.redirect('/milk/my-deliveries')
