import click
from flask.cli import with_appcontext
from flask import Flask
from phaunos.phaunos.routes import phaunos_api
from phaunos.user.routes import user_api
from phaunos.token.routes import token_api
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail
import numpy as np
import wavio
import pathlib
import shutil
import uuid
import os
import random
from flask import jsonify
from phaunos.shared import db, ma, jwt
from phaunos.email_utils import mail


######################################
#### Application Factory Function ####
######################################

def create_app(testing=False):
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    
    if testing:
        app.config['TESTING'] = True

    initialize_extensions(app)
    app.register_blueprint(phaunos_api)
    app.register_blueprint(user_api)
    app.register_blueprint(token_api)
    register_cli(app)
    return app


def initialize_extensions(app):
    db.init_app(app)
    ma.init_app(app)
    mail.init_app(app)
    jwt.init_app(app)
    migrate = Migrate(app, db)


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
        for item in Audio.query.filter(Audio.rel_path.startswith("dummy")).all():
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

        
        # create directory
        pathlib.Path(app.config['DUMMY_DATA_FOLDER']).mkdir(parents=True, exist_ok=True)
        

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
            db.session.add(user)
            db.session.flush()

        # create tags
        for i in range(n_tags):
            tag = Tag()
            tag.name = f'dummy_tag{i}'
            db.session.add(tag)
            db.session.flush()

        tags = Tag.query.all()
        # create tagsets
        for i in range(n_tagsets):
            tagset = Tagset()
            tagset.name = f'dummy_tagset{i}'
            tagset.tags.extend(random.sample(tags, n_tags_per_tagset))
            db.session.add(tagset)
            db.session.flush()

        # create audios
        for i in range(n_audios):
            rel_path = os.path.join(app.config['DUMMY_DATA_FOLDER'], str(uuid.uuid4()) + '.wav')
            create_random_wav(os.path.join(app.config['DUMMY_DATA_FOLDER'], rel_path), duration=5)
            audio = Audio()
            audio.rel_path = rel_path
            db.session.add(audio)
            db.session.flush()

        audios = Audio.query.all()
        tagsets = Tagset.query.all()
        users = User.query.all()
        
        # create projects
        for i in range(n_projects):
            p = Project()
            p.name = f'dummy_project{i}'
            p.audio_root_url = "http://127.0.0.1:5000"
            p.allow_regions = random.choice([True, False])
            # add random audios
            p.audios.extend(random.sample(audios, n_audios_per_project))
            # add random tagsets
            p.tagsets.extend(random.sample(tagsets, n_tagsets_per_project))
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
                    upr.user_role = Role.MEMBER
                else:
                    upr.user_role = Role.ADMIN
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
    

