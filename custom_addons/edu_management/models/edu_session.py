from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, date


class EduSession(models.Model):
    _name = "edu.session"
    _description = "Quản lý buổi học"
    _order = "start_date desc"



    # --- 1. Workflow States ---
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('open', 'Mở đăng ký'),
        ('done', 'Kết thúc'),
        ('cancel', 'Hủy'),
    ], string='Trạng thái', default='draft', required=True, copy=False)

    name = fields.Char(string="Tên buổi học", required=True)
    code = fields.Char(string="Mã buổi học", readonly=True,
                       copy=False, default='New')
    start_date = fields.Date(string='Ngày bắt đầu')
    duration = fields.Float(string='Thời lượng (Ngày)', default=1.0)
    end_date = fields.Date(string="Ngày kết thúc",
                           store=True, compute='_compute_end_date')

    course_id = fields.Many2one('edu.course', string='Khóa học')
    instructor_id = fields.Many2one('res.partner', string='Giảng viên')
    classroom_id = fields.Many2one('edu.classroom', string='Phòng học')
    attendee_ids = fields.Many2many('res.partner', string='Học viên')
    is_this_week = fields.Boolean(compute="_compute_is_this_week", store=True)

    # --- Metrics ---
    attendee_count = fields.Integer(
        string="Số học viên", compute='_compute_attendee_count', store=True)
    taken_seats = fields.Float(
        string="Tỷ lệ lấp đầy", compute='_compute_taken_seats', store=True)
    revenue = fields.Float(string="Doanh thu dự kiến",
                           compute='_compute_revenue', store=True)

    # ============================================================
    # TỐI ƯU: GHI ĐÈ HÀM SEARCH ĐỂ ẨN BUỔI HỌC CỦA GV KHÔNG HOẠT ĐỘNG
    # ============================================================
    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        """ Ẩn buổi học nếu giảng viên bị bỏ tích 'is_instructor' """
        domain += ['|', ('instructor_id', '=', False),
                   ('instructor_id.is_instructor', '=', True)]
        return super(EduSession, self)._search(domain, offset, limit, order, access_rights_uid)

    # ============================================================
    # VALIDATIONS (CONSTRAINS) - ĐÃ CẬP NHẬT KIỂM TRA TRÙNG LỊCH PHÒNG
    # ============================================================
    @api.constrains('name', 'duration', 'attendee_ids', 'classroom_id', 'start_date', 'end_date')
    def _check_session_constraints(self):
        for record in self:
            # 1. Check trùng tên
            if self.search_count([('name', '=', record.name), ('id', '!=', record.id)]) > 0:
                raise ValidationError(
                    _("Tên buổi học '%s' đã tồn tại!") % record.name)

            # 2. Check thời lượng âm
            if record.duration < 0:
                raise ValidationError(
                    _("Thời lượng buổi học không được phép nhỏ hơn 0!"))

            # 3. Check sức chứa phòng
            if record.classroom_id and len(record.attendee_ids) > record.classroom_id.capacity:
                raise ValidationError(_("Phòng '%s' chỉ có tối đa %s chỗ, nhưng bạn đã nhập %s học viên.")
                                      % (record.classroom_id.name, record.classroom_id.capacity, len(record.attendee_ids)))

            # 4. CHECK TRÙNG LỊCH PHÒNG HỌC
            if record.classroom_id and record.start_date and record.end_date:
                overlapping_sessions = self.search([
                    ('id', '!=', record.id),  # Không so sánh với chính nó
                    ('classroom_id', '=', record.classroom_id.id),  # Cùng phòng
                    ('state', '!=', 'cancel'),  # Không tính các lớp đã hủy
                    # Logic kiểm tra chồng lấn thời gian
                    ('start_date', '<=', record.end_date),
                    ('end_date', '>=', record.start_date),
                ])
                if overlapping_sessions:
                    first_conflict = overlapping_sessions[0]
                    raise ValidationError(_(
                        "Xung đột lịch học! Phòng '%s' đã được sử dụng bởi lớp '%s' "
                        "trong khoảng thời gian từ %s đến %s."
                    ) % (record.classroom_id.name, first_conflict.name, first_conflict.start_date, first_conflict.end_date))

    # ============================================================
    # COMPUTE METHODS
    # ============================================================
    @api.depends('attendee_ids')
    def _compute_attendee_count(self):
        for record in self:
            record.attendee_count = len(record.attendee_ids)

    @api.depends('attendee_ids', 'course_id')
    def _compute_revenue(self):
        for record in self:
            fee = getattr(record.course_id, 'tuition_fee', 0.0)
            record.revenue = len(record.attendee_ids) * fee

    @api.depends('start_date', 'duration')
    def _compute_end_date(self):
        for record in self:
            record.end_date = record.start_date + \
                timedelta(days=record.duration) if record.start_date else False

    @api.depends('classroom_id.capacity', 'attendee_ids')
    def _compute_taken_seats(self):
        for record in self:
            cap = record.classroom_id.capacity if record.classroom_id else 0
            record.taken_seats = (
                100.0 * len(record.attendee_ids) / cap) if cap else 0.0

    @api.depends('start_date')
    def _compute_is_this_week(self):
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        for rec in self:
            rec.is_this_week = bool(
                rec.start_date and week_start <= rec.start_date <= week_end)

    # ============================================================
    # ONCHANGE & CRUD
    # ============================================================
    @api.onchange('course_id')
    def _onchange_course_id(self):
        if self.course_id and self.course_id.responsible_id:
            self.instructor_id = self.course_id.responsible_id.partner_id
        else:
            self.instructor_id = False

    @api.model
    def create(self, vals):
        if vals.get('code', 'New') == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code(
                'edu.session') or 'New'
        return super().create(vals)

    def unlink(self):
        for record in self:
            if record.state not in ('draft', 'cancel'):
                raise UserError(
                    _("Chỉ được xóa lớp ở trạng thái Dự thảo hoặc Hủy!"))
        return super().unlink()

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        domain = domain or []
        if name:
            domain = ['|', ('code', operator, name),
                      ('instructor_id.name', operator, name)] + domain
        return self._search(domain, limit=limit, order=order)

    # ============================================================
    # ACTIONS
    # ============================================================
    def action_confirm(self):
        for record in self:
            if not record.classroom_id or not record.instructor_id:
                raise ValidationError(
                    _("Vui lòng bổ sung Phòng học và Giảng viên trước khi xác nhận!"))
            record.state = 'open'

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        for record in self:
            if record.state == 'done':
                raise UserError(_("Không thể hủy lớp đã kết thúc!"))
            record.state = 'cancel'

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {}, state='draft', attendee_ids=[])
        return super().copy(default)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'start_date' in fields_list:
            res.update({'start_date': date.today() + timedelta(days=1)})
        return res
    
    def write(self, vals):
        # Nếu kéo thả đổi ngày bắt đầu trên lịch, ta cần đảm bảo ngày kết thúc vẫn đúng
        res = super(EduSession, self).write(vals)
        return res
