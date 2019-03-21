import os
import re
from flask import current_app, make_response, url_for
from markupsafe import Markup
from flask_admin.contrib.sqla import ModelView
import uuid
from werkzeug.datastructures import FileStorage
from wtforms.validators import ValidationError
from wtforms.fields import SelectMultipleField
from flask_admin import AdminIndexView, BaseView
from flask_admin.contrib import sqla
from flask_admin.form import Select2Widget, FileUploadField

from phaunos.phaunos.models import Tagset, Tag, Project, UserProjectRel, Audio
from phaunos.phaunos.models import validate_audiolist
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



class PhaunosBaseView(BaseView):
    def render(self, template, **kwargs):
        try:
            verify_jwt_in_request()
            self._template_args['current_user'] = get_current_user()
            resp = make_response(super(PhaunosBaseView, self).render(template, **kwargs))

        except ExpiredSignatureError:
            # if the access token has expired, create new non-fresh token
            current_app.logger.info("Access token has expired.")
            try:
                verify_jwt_refresh_token_in_request()
                self._template_args['current_user'] = get_current_user()
                access_token = create_access_token(identity=get_jwt_identity(), fresh=False)
                resp = make_response(super(PhaunosBaseView, self).render(template, **kwargs))
                set_access_cookies(resp, access_token)
            except ExpiredSignatureError:
                # if the refresh token has expired, user must login again
                current_app.logger.info("Refresh token has expired")
                resp = make_response(super(PhaunosBaseView, self).render(template, **kwargs))
                unset_jwt_cookies(resp)
        except NoAuthorizationError:
            current_app.logger.info("No authorization token.")
            resp = make_response(super(PhaunosBaseView, self).render(template, **kwargs))
        return resp


class PhaunosModelView(PhaunosBaseView, ModelView):
    pass


class PhaunosAdminIndexView(PhaunosBaseView, AdminIndexView):
    pass


class UserAdminView(PhaunosModelView):
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
    
    
class TagAdminView(PhaunosModelView):
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


class ProjectAdminView(PhaunosModelView):
    
    column_list = ['name', 'created_by', 'num_annotations']
    

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
