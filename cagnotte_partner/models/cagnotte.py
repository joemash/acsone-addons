# © 2015  Laetitia Gangloff, Acsone SA/NV (http://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class AccountCagnotte(models.Model):
    _inherit = "account.cagnotte"

    partner_id = fields.Many2one(comodel_name="res.partner", string="Partner")

    @api.multi
    def _get_name(self):
        self.ensure_one()
        name = super(AccountCagnotte, self)._get_name()
        if self.partner_id.name:
            return "%s, %s" % (name, self.partner_id.name)
        return name

    @api.constrains("partner_id", "cagnotte_type_id", "active")
    def _check_unique_cagnotte(self):
        for cagnotte in self:
            if not cagnotte.active or not cagnotte.partner_id:
                return True
            res = self.search_count(
                [
                    ("partner_id", "=", cagnotte.partner_id.id),
                    ("cagnotte_type_id", "=", cagnotte.cagnotte_type_id.id),
                    ("active", "=", True),
                    ("id", "!=", cagnotte.id),
                ]
            )
            if res > 0:
                raise ValidationError(
                    _("A cagnotte with cagnotte type and" " partner already exist")
                )
        return True

    @api.constrains("partner_id")
    def _check_partner(self):
        """Check there is no move lines to be able to set a partner"""
        for cagnotte in self:
            if cagnotte.partner_id and cagnotte.account_move_line_ids:
                raise ValidationError(
                    _("Partner can not be defined on a" " cagnotte with journal items")
                )
        return True


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def cagnotte_value(self, values):
        """If partner cagnotte is set on move line,
        set partner to cagnotte partner
        """
        cagnotte_obj = self.env["account.cagnotte"]
        if values.get("account_cagnotte_id"):
            cagnotte = cagnotte_obj.browse(values["account_cagnotte_id"])
            values["partner_id"] = cagnotte.partner_id.id or values.get("partner_id")
        elif values.get("account_id") and values.get("partner_id"):
            # check if account/partner is linked to cagnotte and assign it
            # if it the case
            cagnotte = cagnotte_obj.search(
                [
                    ("cagnotte_type_id.account_id", "=", values["account_id"]),
                    ("partner_id", "=", values["partner_id"]),
                ]
            )
            if cagnotte:
                values["account_cagnotte_id"] = cagnotte.id
            else:
                values = super(AccountMoveLine, self).cagnotte_value(values)
        else:
            values = super(AccountMoveLine, self).cagnotte_value(values)
        return values

    @api.onchange("account_cagnotte_id")
    def onchange_account_cagnotte_id(self):
        """set partner on move line"""
        if self.account_cagnotte_id and self.account_cagnotte_id.partner_id:
            self.partner_id = self.account_cagnotte_id.partner_id
