from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EduClassroom(models.Model):
    _name = "edu.classroom"
    _description = "Quản lý phòng học"

    name = fields.Char(string="Tên phòng học", required=True)
    capacity = fields.Integer(string="Sức chứa", required=True, default=1)

    # Chặn số ghế âm và hiển thị Modal báo lỗi
    @api.constrains('capacity')
    def _check_capacity(self):
        for record in self:
            if record.capacity <= 0:
                # Khi raise ValidationError, Odoo tự động bật Modal báo lỗi màu đỏ
                raise ValidationError(
                    "LỖI CẤU HÌNH: Sức chứa của phòng '%s' phải là số dương (lớn hơn 0)!" % record.name
                )
