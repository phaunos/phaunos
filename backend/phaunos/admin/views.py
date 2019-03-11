import os
import re
from flask import current_app
from flask_admin.contrib.sqla import ModelView
import uuid
from werkzeug.datastructures import FileStorage
from wtforms.validators import ValidationError
from wtforms.fields import SelectMultipleField
from flask_admin.contrib import sqla
from flask_admin.form import Select2Widget, FileUploadField

from phaunos.phaunos.models import Tagset, Tag, Project, UserProjectRel, Audio
from phaunos.phaunos.models import validate_audiolist
from phaunos.user.models import User

from phaunos.shared import db


class UserAdminView(ModelView):
    column_exclude_list = ['password',]
    form_excluded_columns = ['annotations', 'user_project_rel']
    form_widget_args = {
        'password':{
            'disabled': True
        },
        'confirmed_on':{
            'disabled': True
        },
        'projects':{
            'disabled': True
        },
    }

    def get_edit_form(self):
        form = super(UserAdminView, self).get_edit_form()
        form.projects = sqla.fields.QuerySelectMultipleField("Projects")
        return form

    def edit_form(self, obj=None):
        form = super(UserAdminView, self).edit_form(obj)
        form.projects.render_kw = {'style':'color:#456456'}
        form.projects.query = db.session.query(Project).join(UserProjectRel) \
            .filter(UserProjectRel.user_id==obj.id).all()
        form.projects.data = form.projects.query
        current_app.logger.info(form.projects.__dict__)
        current_app.logger.info(form.projects.__html__())
        current_app.logger.info("|".join([p(**{'style': 'font-size:50px;'}) for p in form.projects]))
        current_app.logger.info(form.projects.__html__())
        return form
    
    

class TagAdminView(ModelView):
    column_exclude_list = ['annotations',]
    form_excluded_columns = ['annotations',]
    form_widget_args = {
        'tagsets':{
            'disabled': True
        }
    }


class TagsetAdminView(ModelView):
    form_widget_args = {
        'projects':{
            'disabled': True
        }
    }


class ProjectAdminView(ModelView):
    form_excluded_columns = ['annotations', 'user_project_rel']
    
    def get_create_form(self):
        form = super(ProjectAdminView, self).get_create_form()
        form.audiolist_filename = FileUploadField(
            base_path=os.path.join(current_app.config['UPLOAD_FOLDER'], 'audiolist_filenames'),
            allow_overwrite=False,
            namegen=random_name,
            validators=[validate_audiolistfile])
        form.taglist_filename = FileUploadField(
            base_path=os.path.join(current_app.config['UPLOAD_FOLDER'], 'taglist_filenames'),
            allow_overwrite=False,
            namegen=random_name,
        )
#            validators=[validate_taglistfile])
        return form

    def get_edit_form(self):
        form = super(ProjectAdminView, self).get_edit_form()
        form.users = sqla.fields.QuerySelectMultipleField("Users", allow_blank=True)
        return form

    def edit_form(self, obj=None):
        form = super(ProjectAdminView, self).edit_form(obj)
        form.users.query = User.query
        form.users.data = db.session.query(User).join(UserProjectRel) \
            .filter(UserProjectRel.project_id==obj.id).all()
        return form


def random_name(obj, file_data):
    return str(uuid.uuid4()) + ".csv"


def validate_audiolistfile(form, field):
    data = field.data
    if data and isinstance(data, FileStorage):
        error = validate_audiolist(data.stream)
        if error:
            raise ValidationError(error)


def validate_taglistfile(form, field):
    data = field.data
    if data and isinstance(data, FileStorage):
        error = validate_taglist(data.stream)
        if error:
            raise ValidationError(error)
