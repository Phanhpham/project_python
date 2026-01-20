from odoo import models, fields


class EduSubject(models.Model):
    _name = "edu.subject"
    _description = "Educational Subject"

    name = fields.Char(string="Tên môn học", required=True)
    code = fields.Char(string="Mã môn học", required=True)
    description = fields.Text(string="Mô tả môn học")

    course_ids = fields.One2many(
        'edu.course',
        'subject_id',
        string='Courses'
    )