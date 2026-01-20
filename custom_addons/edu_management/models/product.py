from odoo import models, fields


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = "product.template"

    is_edu_fee = fields.Boolean(string="Đã đóng học phí chưa?", 
                                default=False)
    list_price = fields.Float(string="Giá niêm yết (học phí)", 
                              default=0.0)