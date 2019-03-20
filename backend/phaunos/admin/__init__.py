from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from phaunos.phaunos.models import Tagset, Tag, Project, Annotation
from phaunos.user.models import User
from phaunos.shared import db
from .views import (
    PhaunosAdminIndexView,
    TagAdminView,
    TagsetAdminView,
    ProjectAdminView,
    UserAdminView,
)


admin = Admin(
    index_view=PhaunosAdminIndexView(),
    name='phaunos',
    template_mode='bootstrap3',
    base_template='admin/phaunos_base.html'
)
