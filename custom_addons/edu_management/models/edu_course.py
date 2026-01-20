from odoo import models, fields, api

from odoo.exceptions import ValidationError


class EduCourse(models.Model):
    _name = "edu.course"
    _description = "Quản lý khóa học"

    name = fields.Char(string="Tên khóa học", required=True)
    # --- THÊM TRƯỜNG HỌC PHÍ ĐỂ TÍNH DOANH THU (MỤC 9) ---
    tuition_fee = fields.Float(string="Học phí", default=0.0)

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Tên khóa học đã tồn tại!'),
    ]

    description = fields.Text(string="Mô tả khóa học")
    active = fields.Boolean(string="Active", default=True)

    level = fields.Selection(
        string="Chọn level khóa học",
        selection=[('basic', 'Basic'), ('adv', 'Adv')],
    )

    subject_id = fields.Many2one("edu.subject", string="Môn học")
    
    # --- SỬA TẠI ĐÂY: Thêm domain lọc để chỉ hiện những người đang tích 'Là giảng viên' ---
    responsible_id = fields.Many2one(
        'res.users', 
        string='Người phụ trách',
        domain="[('partner_id.is_instructor', '=', True)]"
    )
    # ---------------------------------------------------------------------------------

    session_ids = fields.One2many(
        'edu.session', 'course_id', string='Danh sách lớp')

    session_count = fields.Integer(
        string="Số lượng lớp", compute="_compute_session_count")

    @api.constrains('tuition_fee')
    def _check_tuition_fee(self):
        for record in self:
            if record.tuition_fee < 0:
                raise ValidationError(
                    "Học phí không được phép nhỏ hơn 0. Vui lòng kiểm tra lại!")

    @api.depends('session_ids')
    def _compute_session_count(self):
        for record in self:
            record.session_count = len(record.session_ids)

    def action_view_sessions(self):
        return {
            'name': 'Danh sách lớp học',
            'type': 'ir.actions.act_window',
            'res_model': 'edu.session',
            'view_mode': 'tree,form',
            'domain': [('course_id', '=', self.id)],
            'context': {'default_course_id': self.id},
            'target': 'current',
        }