from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from phaunos.phaunos.models import Tagset, Tag, Project, Annotation
from phaunos.user.models import User
from phaunos.shared import db
from .views import (
    TagAdminView,
    TagsetAdminView,
    ProjectAdminView,
    UserAdminView,
)


admin = Admin(name='phaunos', template_mode='bootstrap3')
