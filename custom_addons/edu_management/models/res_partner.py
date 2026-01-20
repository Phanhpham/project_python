from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_instructor = fields.Boolean(string='Là giảng viên', default=False)
    session_teaching_ids = fields.One2many('edu.session', 'instructor_id', string='Lớp đang dạy')
    session_attending_ids = fields.Many2many('edu.session', string='Lớp đang học')

    # Phải có field này để Smart Button hiển thị số liệu
    session_teaching_count = fields.Integer(
        string="Số lớp giảng dạy", 
        compute="_compute_session_teaching_count"
    )

    # --- SỬA LOGIC: Chỉ đếm các lớp có trạng thái khác 'done' ---
    @api.depends('session_teaching_ids.state')
    def _compute_session_teaching_count(self):
        for record in self:
            # Lọc danh sách: chỉ lấy những lớp mà instructor_id là mình và trạng thái không phải kết thúc
            active_sessions = record.session_teaching_ids.filtered(lambda s: s.state != 'done')
            record.session_teaching_count = len(active_sessions)

    # --- SỬA LOGIC: Chỉ hiển thị các lớp có trạng thái khác 'done' khi bấm vào nút ---
    def action_view_teaching_sessions(self):
        self.ensure_one()
        return {
            'name': 'Lớp học đang giảng dạy',
            'type': 'ir.actions.act_window',
            'res_model': 'edu.session',
            'view_mode': 'tree,form',
            # Thêm điều kiện lọc trạng thái khác 'done' vào domain
            'domain': [('instructor_id', '=', self.id), ('state', '!=', 'done')],
            'context': {'default_instructor_id': self.id},
            'target': 'current',
        }