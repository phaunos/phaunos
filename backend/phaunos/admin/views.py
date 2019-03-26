import os
import re
from flask import current_app, make_response, url_for, request
from markupsafe import Markup
from flask_admin.contrib.sqla import ModelView
import uuid
from werkzeug.datastructures import FileStorage
from wtforms.validators import ValidationError
from wtforms.fields import Field, SelectMultipleField, StringField
from wtforms.widgets import html_params, TextInput
from flask_admin import AdminIndexView, BaseView, expose
from flask_admin.contrib import sqla
from flask_admin.form import Select2Widget, FileUploadField, rules

from phaunos.phaunos.models import Tagset, Tag, Project, UserProjectRel, Audio
from phaunos.phaunos.models import validate_audiolist, validate_taglist
from phaunos.user.models import User

from phaunos.shared import db

from flask_jwt_extended import (
    get_current_user,
    get_jwt_identity,
    verify_jwt_in_request,
    verify_jwt_refresh_token_in_request,
    create_access_token,
    set_access_cookies,
    unset_jwt_cookies,
)
from flask_jwt_extended.exceptions import NoAuthorizationError
from jwt import ExpiredSignatureError



class PhaunosModelView(ModelView):

    def render(self, template, **kwargs):
        try:
            verify_jwt_in_request()
            self._template_args['current_user'] = get_current_user()
            resp = make_response(super(PhaunosModelView, self).render(template, **kwargs))

        except ExpiredSignatureError:
            # if the access token has expired, create new non-fresh token
            current_app.logger.info("Access token has expired.")
            try:
                verify_jwt_refresh_token_in_request()
                self._template_args['current_user'] = get_current_user()
                access_token = create_access_token(identity=get_jwt_identity(), fresh=False)
                resp = make_response(super(PhaunosModelView, self).render(template, **kwargs))
                set_access_cookies(resp, access_token)
            except ExpiredSignatureError:
                # if the refresh token has expired, user must login again
                current_app.logger.info("Refresh token has expired")
                resp = make_response(super(PhaunosModelView, self).render(template, **kwargs))
                unset_jwt_cookies(resp)
        except NoAuthorizationError:
            current_app.logger.info("No authorization token.")
            resp = make_response(super(PhaunosModelView, self).render(template, **kwargs))
        return resp

    def is_visible(self):
        if request.path == url_for('admin_signup.index'):
            return False
        return True


class PhaunosBaseView(BaseView):
    pass


class PhaunosAdminIndexView(AdminIndexView):
    def is_visible(self):
        return False

class SignupView(BaseView):

    @expose('/')
    def index(self):
        return self.render('admin/signup.html')

    def is_visible(self):
        if request.path == url_for('admin_signup.index'):
            return True
        return False



class UserAdminView(PhaunosModelView):
    category='dude'
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
        return form
    
    
class TagAdminView(PhaunosModelView):
    category='dude'
    column_exclude_list = ['annotations',]
    form_excluded_columns = ['annotations',]
    form_widget_args = {
        'tagsets':{
            'disabled': True
        }
    }


class TagsetAdminView(PhaunosModelView):
    form_widget_args = {
        'projects':{
            'disabled': True
        }
    }


class DownloadFileWidget(TextInput):
    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        kwargs.setdefault("type", self.input_type)
        if "value" not in kwargs:
            kwargs["value"] = field._value()
        if "required" not in kwargs and "required" in getattr(field, "flags", []):
            kwargs["required"] = True
        html = "<input %s>" % self.html_params(name=field.name, **kwargs)
        url = url_for('bp_api.uploaded', filename=field._value())
        html +=  f'<a href="{url}">Download</a>'
        return Markup(html)




class ProjectAdminView(PhaunosModelView):
    
    column_list = ['name', 'created_by', 'num_annotations']

    form_create_rules = ('name', 'visualization_type',
                       'allow_regions',
                       'audiolist_filename', 'taglist_filename')
    
    form_edit_rules = ('name', 'created_by', 'visualization_type',
                       'allow_regions', 'tagsets', 'users',
                       'audiolist_filename', 'taglist_filename')

    def _get_annotations(view, context, project, name):



        _html = '''<form action="{url}" method="get">
                <input id="project_id" name="project_id"  type="hidden" value="{project_id}">
                <input id="web" name="web"  type="hidden" value=1>
                <button type='submit'>Download annotations</button>
            </form> ({perc}% completed)
        '''.format(url=url_for('bp_api.annotations'), project_id=project.id, perc=project.percentage_of_completion)

        return Markup(_html)

    column_formatters = {
        'num_annotations': _get_annotations
    }
    
    def get_create_form(self):
        form = super(ProjectAdminView, self).get_create_form()
        form.audiolist_filename = FileUploadField(
            base_path=current_app.config['FILE_FOLDER'],
            relative_path=os.path.join(current_app.config['UPLOAD_FOLDER'] , 'audiolist_files/'),
            allow_overwrite=False,
            namegen=random_name,
            validators=[validate_audiolistfile])
        form.taglist_filename = FileUploadField(
            base_path=current_app.config['FILE_FOLDER'],
            relative_path=os.path.join(current_app.config['UPLOAD_FOLDER'], 'taglist_files/'),
            allow_overwrite=False,
            namegen=random_name,
            validators=[validate_taglistfile]
        )
        return form

    def get_edit_form(self):
        form = super(ProjectAdminView, self).get_edit_form()
        form.users = sqla.fields.QuerySelectMultipleField("Users", allow_blank=True)
        form.audiolist_filename = StringField(widget=DownloadFileWidget(), render_kw={'disabled': True})
        form.taglist_filename = StringField(widget=DownloadFileWidget(), render_kw={'disabled': True})
        return form

    def edit_form(self, obj=None):
        form = super(ProjectAdminView, self).edit_form(obj)
        form.created_by.render_kw = {'disabled': True}
        form.users.query = User.query
        form.users.data = db.session.query(User).join(UserProjectRel) \
            .filter(UserProjectRel.project_id==obj.id).all()
        return form


def random_name(obj, file_data):
    current_app.logger.info("in random_name")
    current_app.logger.info(obj.__dict__)
    current_app.logger.info(file_data.filename)
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
