from odoo import fields, http
from odoo.http import request

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f2f5;min-height:100vh}
.dh{background:linear-gradient(135deg,#1a1a5e 0%,#6c3fc5 100%);padding:16px 20px;position:sticky;top:0;z-index:99;box-shadow:0 4px 12px rgba(0,0,0,.3)}
.dh-title{color:#fff;font-size:20px;font-weight:900}
.dh-sub{color:rgba(255,255,255,.8);font-size:12px;margin-top:4px}
.prog-wrap{background:#fff;padding:14px 16px;border-bottom:1px solid #e8eaed}
.prog-label{display:flex;justify-content:space-between;font-size:13px;font-weight:600;margin-bottom:6px}
.prog-count{color:#28a745;font-weight:800}
.prog-bar{background:#e9ecef;border-radius:10px;height:10px}
.prog-fill{background:linear-gradient(90deg,#28a745,#20c997);height:10px;border-radius:10px}
.card{background:#fff;margin:12px;border-radius:16px;box-shadow:0 2px 12px rgba(0,0,0,.09);overflow:hidden}
.card-pending{border-left:5px solid #6c3fc5}
.card-delivered{border-left:5px solid #28a745;opacity:.85}
.card-skipped{border-left:5px solid #ffc107;opacity:.85}
.card-absent{border-left:5px solid #dc3545;opacity:.85}
.card-top{padding:14px 16px 8px;display:flex;align-items:flex-start;gap:12px}
.stop-badge{min-width:36px;height:36px;background:linear-gradient(135deg,#1a1a5e,#6c3fc5);color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:13px;flex-shrink:0}
.cust-name{font-size:17px;font-weight:800;color:#1a1a5e;line-height:1.2}
.cust-addr{font-size:12px;color:#888;margin-top:2px}
.status-pill{margin-left:auto;flex-shrink:0;font-size:11px;font-weight:700;padding:4px 12px;border-radius:20px;white-space:nowrap}
.sp-pending{background:#ede8ff;color:#5a2fc2}
.sp-delivered{background:#d4edda;color:#155724}
.sp-skipped{background:#fff3cd;color:#856404}
.sp-absent{background:#f8d7da;color:#721c24}
.prod-row{padding:2px 16px 10px 64px;font-size:13px;color:#555}
.note-row{margin:0 16px 10px;background:#fffde7;border-radius:8px;padding:8px 12px;font-size:12px;color:#6d5c00;border-left:3px solid #ffc107}
.actions{display:flex;gap:8px;padding:8px 16px 16px}
.btn-d{flex:2;background:#28a745;color:#fff;border:none;border-radius:12px;padding:14px 10px;font-size:15px;font-weight:700;cursor:pointer}
.btn-s{flex:1;background:#fff3cd;color:#856404;border:2px solid #ffc107;border-radius:12px;padding:14px 6px;font-size:13px;font-weight:700;cursor:pointer}
.btn-a{flex:1;background:#f8d7da;color:#721c24;border:2px solid #dc3545;border-radius:12px;padding:14px 6px;font-size:13px;font-weight:700;cursor:pointer}
.btn-undo{display:block;width:calc(100% - 32px);margin:0 16px 16px;background:#f8f9fa;color:#6c757d;border:1px solid #dee2e6;border-radius:12px;padding:11px;font-size:13px;cursor:pointer;text-align:center}
.empty{text-align:center;padding:80px 30px;color:#888}
.empty-icon{font-size:56px;margin-bottom:12px}
.empty h3{font-size:20px;color:#555;margin-bottom:8px}
.done-card{background:#fff;margin:12px;border-radius:16px;padding:32px;text-align:center;box-shadow:0 2px 12px rgba(0,0,0,.09)}
.done-title{color:#28a745;font-size:22px;font-weight:900;margin:10px 0 6px}
"""


def _html(body, title="Driver App"):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1"/>
<meta name="theme-color" content="#1a1a5e"/>
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>{body}</body>
</html>"""


def _action_form(token, delivery_id, action, label, css_class):
    return (f'<form action="/milk/driver/{token}/action" method="POST" style="display:contents">'
            f'<input type="hidden" name="delivery_id" value="{delivery_id}"/>'
            f'<input type="hidden" name="action" value="{action}"/>'
            f'<button type="submit" class="{css_class}">{label}</button>'
            f'</form>')


class MilkDriverPortal(http.Controller):

    @http.route('/milk/driver/<string:token>', type='http', auth='public',
                website=False, sitemap=False)
    def driver_portal(self, token, **kwargs):
        route = request.env['tr.milk.route'].sudo().search(
            [('access_token', '=', token)], limit=1)
        if not route:
            body = '<div class="empty"><div class="empty-icon">&#128274;</div><h3>Invalid Link</h3><p>Ask your manager for a new driver link.</p></div>'
            return request.make_response(_html(body, "Invalid Link"),
                                         headers=[('Content-Type', 'text/html; charset=utf-8')])

        today = fields.Date.today()
        sheet = request.env['tr.milk.delivery.sheet'].sudo().search([
            ('route_id', '=', route.id),
            ('delivery_date', '=', today),
        ], limit=1)

        deliveries = sheet.delivery_ids.sorted('sequence') if sheet else \
            request.env['tr.milk.delivery'].sudo()

        total = len(deliveries)
        delivered = len(deliveries.filtered(lambda d: d.state == 'delivered'))
        pct = int(delivered * 100 / total) if total else 0

        # Header
        parts = [
            f'<div class="dh">'
            f'<div class="dh-title">&#127843; {route.name}</div>'
            f'<div class="dh-sub">&#128100; {route.driver_id.name} &nbsp;&#183;&nbsp; &#128197; {today}</div>'
            f'</div>',

            f'<div class="prog-wrap">'
            f'<div class="prog-label"><span>Progress</span>'
            f'<span class="prog-count">{delivered}/{total} Done</span></div>'
            f'<div class="prog-bar"><div class="prog-fill" style="width:{pct}%"></div></div>'
            f'</div>',
        ]

        if not sheet or total == 0:
            parts.append(
                '<div class="empty">'
                '<div class="empty-icon">&#128203;</div>'
                '<h3>No Deliveries Today</h3>'
                '<p>No delivery sheet found for today.<br/>Ask the manager to generate it.</p>'
                '</div>'
            )
        elif delivered == total:
            parts.append(
                '<div class="done-card">'
                '<div style="font-size:56px">&#127881;</div>'
                f'<div class="done-title">Route Complete!</div>'
                f'<p style="color:#666">All <strong>{total}</strong> deliveries done. Great work!</p>'
                '</div>'
            )

        for i, d in enumerate(deliveries):
            state = d.state
            state_labels = {
                'pending': '&#9201; Pending',
                'delivered': '&#10003; Done',
                'skipped': 'Skipped',
                'absent': 'Absent',
            }
            note = d.subscription_id.note if d.subscription_id else ''
            addr = d.partner_id.street or ''
            card = (
                f'<div class="card card-{state}">'
                f'  <div class="card-top">'
                f'    <div class="stop-badge">{i+1}</div>'
                f'    <div style="flex:1">'
                f'      <div class="cust-name">{d.partner_id.name}</div>'
                f'      <div class="cust-addr">{addr}</div>'
                f'    </div>'
                f'    <span class="status-pill sp-{state}">{state_labels.get(state, state)}</span>'
                f'  </div>'
                f'  <div class="prod-row">&#128230; {d.product_id.name} &nbsp;&#183;&nbsp; '
                f'Qty: <strong>{d.qty} {d.product_id.uom_id.name}</strong> &nbsp;&#183;&nbsp; '
                f'<strong>{d.subtotal:.2f}</strong></div>'
            )
            if note:
                card += f'<div class="note-row">&#128205; {note}</div>'

            if state == 'pending':
                card += (
                    f'<div class="actions">'
                    + _action_form(token, d.id, 'deliver', '&#10003; Delivered', 'btn-d')
                    + _action_form(token, d.id, 'skip', 'Skip', 'btn-s')
                    + _action_form(token, d.id, 'absent', 'Absent', 'btn-a')
                    + '</div>'
                )
            else:
                card += (
                    f'<form action="/milk/driver/{token}/action" method="POST">'
                    f'<input type="hidden" name="delivery_id" value="{d.id}"/>'
                    f'<input type="hidden" name="action" value="reset"/>'
                    f'<button type="submit" class="btn-undo">&#8617; Undo</button>'
                    f'</form>'
                )

            card += '</div>'
            parts.append(card)

        parts.append('<div style="height:48px"></div>')

        return request.make_response(
            _html(''.join(parts), f'{route.name} — Driver App'),
            headers=[('Content-Type', 'text/html; charset=utf-8')]
        )

    @http.route('/milk/driver/<string:token>/action', type='http',
                auth='public', methods=['POST'], csrf=False, website=False)
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
