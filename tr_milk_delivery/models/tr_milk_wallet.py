from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MilkWallet(models.Model):
    _name = 'tr.milk.wallet'
    _description = 'Customer Milk Wallet'
    _inherit = ['mail.thread']
    _rec_name = 'partner_id'

    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        ondelete='restrict', index=True)
    balance = fields.Float(
        string='Balance', compute='_compute_balance',
        store=True, digits=(16, 2))
    transaction_ids = fields.One2many(
        'tr.milk.wallet.transaction', 'wallet_id', string='Transactions')
    transaction_count = fields.Integer(
        compute='_compute_transaction_count', string='Transactions')
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('partner_unique', 'UNIQUE(partner_id)',
         'A wallet already exists for this customer.'),
    ]

    @api.depends('transaction_ids.amount', 'transaction_ids.type')
    def _compute_balance(self):
        for wallet in self:
            credits = sum(wallet.transaction_ids.filtered(
                lambda t: t.type == 'credit').mapped('amount'))
            debits = sum(wallet.transaction_ids.filtered(
                lambda t: t.type == 'debit').mapped('amount'))
            wallet.balance = credits - debits

    def _compute_transaction_count(self):
        for wallet in self:
            wallet.transaction_count = len(wallet.transaction_ids)

    def action_deposit(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Deposit'),
            'res_model': 'tr.milk.wallet.deposit',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_wallet_id': self.id},
        }

    def deduct(self, amount, description='Delivery', delivery_id=None):
        """Deduct amount from wallet. Returns True if successful."""
        self.ensure_one()
        if self.balance < amount:
            return False
        vals = {
            'wallet_id': self.id,
            'type': 'debit',
            'amount': amount,
            'description': description,
            'date': fields.Date.today(),
        }
        if delivery_id:
            vals['delivery_id'] = delivery_id
        self.env['tr.milk.wallet.transaction'].create(vals)
        return True

    @api.model
    def get_or_create(self, partner_id):
        wallet = self.search([('partner_id', '=', partner_id)], limit=1)
        if not wallet:
            wallet = self.create({'partner_id': partner_id})
        return wallet


class MilkWalletTransaction(models.Model):
    _name = 'tr.milk.wallet.transaction'
    _description = 'Wallet Transaction'
    _order = 'date desc, id desc'

    wallet_id = fields.Many2one(
        'tr.milk.wallet', string='Wallet', required=True, ondelete='cascade')
    partner_id = fields.Many2one(
        related='wallet_id.partner_id', string='Customer', store=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    type = fields.Selection([
        ('credit', 'Deposit'),
        ('debit', 'Delivery Deduction'),
    ], string='Type', required=True)
    amount = fields.Float(string='Amount', required=True, digits=(16, 2))
    description = fields.Char(string='Description')
    delivery_id = fields.Many2one('tr.milk.delivery', string='Delivery')
    currency_id = fields.Many2one(
        related='wallet_id.currency_id', string='Currency')


class MilkWalletDeposit(models.TransientModel):
    _name = 'tr.milk.wallet.deposit'
    _description = 'Add Wallet Deposit'

    wallet_id = fields.Many2one('tr.milk.wallet', required=True)
    partner_id = fields.Many2one(related='wallet_id.partner_id', string='Customer')
    amount = fields.Float(string='Deposit Amount', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    description = fields.Char(string='Note', default='Customer Deposit')

    def action_confirm(self):
        self.ensure_one()
        if self.amount <= 0:
            raise UserError(_('Deposit amount must be positive.'))
        self.env['tr.milk.wallet.transaction'].create({
            'wallet_id': self.wallet_id.id,
            'type': 'credit',
            'amount': self.amount,
            'date': self.date,
            'description': self.description,
        })
        self.wallet_id.message_post(
            body=_('Deposit of %s added. New balance: %s',
                   self.amount, self.wallet_id.balance))
        return {'type': 'ir.actions.act_window_close'}
