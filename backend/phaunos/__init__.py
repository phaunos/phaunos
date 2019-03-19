import click
import datetime
from flask.cli import with_appcontext
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail
import numpy as np
import wavio
import shutil
import uuid
import os
import random
from flask import jsonify
from flask_login import LoginManager
from phaunos.shared import db, ma, jwt, bp_api, bp_admin_auth
from phaunos.email_utils import mail
from phaunos.admin import admin
#from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from phaunos.phaunos.models import Tagset, Tag, Project, Annotation
from phaunos.user.models import User
from phaunos.admin.views import (
    TagAdminView,
    TagsetAdminView,
    ProjectAdminView,
    UserAdminView,
)
from phaunos.user import api
from phaunos.phaunos import api


######################################
#### Application Factory Function ####
######################################


#login_manager = LoginManager()


def create_app(testing=False):
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    
    if testing:
        app.config['TESTING'] = True

    initialize_extensions(app)
    app.register_blueprint(bp_api)
    app.register_blueprint(bp_admin_auth)
    register_cli(app)
    return app


def initialize_extensions(app):
    db.init_app(app)
    migrate = Migrate(app, db)
    ma.init_app(app)
    mail.init_app(app)
    jwt.init_app(app)
#    login_manager.init_app(app)

    admin.init_app(app)
    with app.app_context():
        admin.add_view(TagAdminView(Tag, db.session))
        admin.add_view(TagsetAdminView(Tagset, db.session))
        admin.add_view(ProjectAdminView(Project, db.session))
        admin.add_view(UserAdminView(User, db.session))


################
## Custom CLI ##
################

def register_cli(app):
    
    @app.cli.command()
    def delete_dummy_data():
        
        from phaunos.shared import db
        from phaunos.phaunos.models import (
            Project,
            UserProjectRel,
            Tag,
            Tagset,
            Audio,
            Annotation)
        from phaunos.user.models import User
        
        
        # delete dummy Annotation
        for item in UserProjectRel.query.join(UserProjectRel.project).filter(Project.name.startswith('dummy')).all():
            db.session.delete(item)
        
        # delete dummy UserProjectRel
        for item in UserProjectRel.query.join(UserProjectRel.project).filter(Project.name.startswith('dummy')).all():
            db.session.delete(item)
        
        # delete dummy User
        for item in User.query.filter(User.username.startswith("dummy")).all():
            db.session.delete(item)

        # delete dummy Tag
        for item in Tag.query.filter(Tag.name.startswith("dummy")).all():
            db.session.delete(item)
        
        # delete dummy Tagset
        for item in Tagset.query.filter(Tagset.name.startswith("dummy")).all():
            db.session.delete(item)
        
        # delete dummy Audio
        for item in Audio.query.filter(Audio.path.startswith("dummy")).all():
            db.session.delete(item)
        
        # delete dummy Project
        for item in Project.query.filter(Project.name.startswith("dummy")).all():
            db.session.delete(item)

        
        db.session.commit()

        # delete dummy data folder
        shutil.rmtree(app.config['DUMMY_DATA_FOLDER'], ignore_errors=True)


    @app.cli.command()
    def put_dummy_data():
        
        from phaunos.shared import db
        from phaunos.phaunos.models import (
            Project,
            UserProjectRel,
            Role,
            Tag,
            Tagset,
            Audio,
            Annotation)
        from phaunos.user.models import User


        n_tagsets = 20
        n_tags = 80
        n_users = 100
        n_projects = 20
        n_audios = 100
        n_audios_per_project = 20
        n_users_per_project = 5
        n_tags_per_tagset = 4
        n_tagsets_per_project = 5
        n_annotators_per_audio = 3
        n_annotations_per_annotator_per_audio = 5
        audio_duration = 5
        min_annotation_size=0.2

        # create users
        for i in range(n_users):
            user = User(f'dummy_user{i}', f'user{i}@gmail.com', f'user{i}')
            user.confirmed_on = datetime.datetime.now()
            db.session.add(user)
            db.session.flush()
        users = User.query.all()

        # create tags
        for i in range(n_tags):
            tag = Tag()
            tag.name = f'dummy_tag{i}'
            tag.created_by = random.choice(users)
            db.session.add(tag)
            db.session.flush()
        tags = Tag.query.all()

        # create tagsets
        for i in range(n_tagsets):
            tagset = Tagset()
            tagset.name = f'dummy_tagset{i}'
            tagset.tags.extend(random.sample(tags, n_tags_per_tagset))
            tagset.created_by = random.choice(users)
            db.session.add(tagset)
            db.session.flush()
        tagsets = Tagset.query.all()

        # create audios
        audio_path = os.path.join(app.config['DUMMY_DATA_FOLDER'], 'audio_files')
        os.makedirs(audio_path, exist_ok=True)
        for i in range(n_audios):
            path = os.path.join(audio_path, str(uuid.uuid4()) + '.wav')
            create_random_wav(path, duration=5)
            audio = Audio()
            audio.path = path
            audio.created_by = random.choice(users)
            db.session.add(audio)
            db.session.flush()
        audios = Audio.query.all()
        
        # create audio list files
        audiolist_filenames = []
        audiolist_path = os.path.join(app.config['DUMMY_DATA_FOLDER'], 'audiolist_files')
        os.makedirs(audiolist_path, exist_ok=True)
        for i in range(n_projects):
            audiolist_filename = os.path.join(audiolist_path,  str(uuid.uuid4()) + '.csv')
            with open(audiolist_filename, 'w') as audiolist_file:
                for a in random.sample(audios, n_audios_per_project):
                    audiolist_file.write(a.path + '\n')
            audiolist_filenames.append(audiolist_filename)
        
        
        # create tag list files
        taglist_filenames = []
        taglist_path = os.path.join(app.config['DUMMY_DATA_FOLDER'], 'taglist_files')
        os.makedirs(taglist_path, exist_ok=True)
        for i in range(n_projects):
            taglist_filename = os.path.join(taglist_path,  str(uuid.uuid4()) + '.csv')
            with open(taglist_filename, 'w') as taglist_file:
                for tagset in random.sample(tagsets, n_tagsets_per_project):
                    for tag in tagset.tags:
                        taglist_file.write(tagset.name + ',' + tag.name + '\n')
            taglist_filenames.append(taglist_filename)

        # create projects
        for i in range(n_projects):
            p = Project()
            p.name = f'dummy_project{i}'
            p.audio_root_url = "http://127.0.0.1:5000"
            p.allow_regions = random.choice([True, False])
            p.audiolist_filename = random.choice(audiolist_filenames)
            p.taglist_filename = random.choice(taglist_filenames)
            p.created_by = random.choice(users)
            db.session.add(p)
            db.session.flush()
            # add users
            p_users = random.sample(users, n_users_per_project)
            has_admin = False
            for u in p_users:
                upr = UserProjectRel()
                upr.project_id = p.id
                upr.user_id =u.id
                if has_admin:
                    upr.user_role = Role.PROJECTMEMBER
                else:
                    upr.user_role = Role.PROJECTADMIN
                    has_admin = True
                db.session.add(upr)
                db.session.flush()


        projects = Project.query.all()

        # create annotations
        for p in projects:
            audios = Audio.query.filter(Audio.projects.any(Project.id==p.id)).all()
            user_ids = [upr.user_id for upr in p.user_project_rel]
            for audio in audios:
                annotators = User.query.filter(User.id.in_(user_ids)).all()
                for annotator in annotators:
                    for i in range(n_annotations_per_annotator_per_audio):
                        for tagset in p.tagsets:
                            annotation = Annotation()
                            annotation.start_time = random.uniform(0, audio_duration - min_annotation_size)
                            annotation.end_time = random.uniform(annotation.start_time + min_annotation_size, audio_duration)
                            annotation.tag_id = random.choice(tagset.tags).id
                            annotation.project_id = p.id
                            annotation.audio_id = audio.id
                            annotation.user_id = annotator.id
                            db.session.add(annotation)

        db.session.commit()


def create_random_wav(filename, sr=11025, duration=2):
    x = np.random.rand(duration * sr) * 2 - 1
    wavio.write(filename, x, sr, sampwidth=2)
    

