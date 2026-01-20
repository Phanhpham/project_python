{
    'name': 'Education Management',
    'version': '1.0',
    'summary': 'Hệ thống quản lý giáo dục, học sinh và khóa học',
    'category': 'Education',
    # Phụ thuộc vào base và product để quản lý học phí
    'depends': ['base', 'product'],
    'data': [
        'security/edu_group.xml',
        'security/edu_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/edu_course_views.xml',
        'views/res_partner_views.xml',
        'views/product_views.xml',  
        'views/edu_menus.xml',
        'views/edu_session_views.xml',
        'views/edu_classroom_views.xml'
    ],
    'installable': True,
    'application': True,
    'license': "LGPL-3"
}
