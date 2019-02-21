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


#######################
#### Configuration ####
#######################

# Create the instances of the Flask extensions (flask-sqlalchemy, flask-login, etc.) in
# the global scope, but without any arguments passed in.  These instances are not attached
# to the application at this point.
#db = SQLAlchemy()


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
                Tag,
                Tagset,
                Audio,
                Annotation
                )
        from phaunos.user.models import User
        
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

        # delete dummy UserProjectRel
        for item in UserProjectRel.query.join(UserProjectRel.project).filter(Project.name.startswith('dummy')).all():
            db.session.delete(item)

        db.session.commit()

        # delete dummy data folder
        shutil.rmtree(app.config['DUMMY_DATA_FOLDER'], ignore_errors=True)


    @app.cli.command()
    def put_dummy_data():
        
        from phaunos.shared import db
        from phaunos.phaunos.models import (
                Project,
                Tag,
                Tagset,
                Audio,
                Annotation
                )
        from phaunos.user.models import User

        
        # create directory
        pathlib.Path(app.config['DUMMY_DATA_FOLDER']).mkdir(parents=True, exist_ok=True)
        

        n_tagsets = 30
        n_tags = 80 # per tagsets
        n_users = 10
        n_projects = 20
        n_audios = 100
        n_audios_per_project = 10
        n_tags_per_tagset = 4
        n_tagsets_per_project = 5
        n_annotations = 1000

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
            create_random_wav(os.path.join(app.config['DUMMY_DATA_FOLDER'], rel_path))
            audio = Audio()
            audio.rel_path = rel_path
            db.session.add(audio)
            db.session.flush()

        audios = Audio.query.all()
        tagsets = Tagset.query.all()
        # create projects
        for i in range(n_projects):
            project = Project()
            project.name = f'dummy_project{i}'
            project.audio_root_url = "http://127.0.0.1:5000"
            project.allow_regions = random.choice([True, False])
            # get random audios
            project.audios.extend(random.sample(audios, n_audios_per_project))
            # get random tagsets
            project.tagsets.extend(random.sample(tagsets, n_tagsets_per_project))
            db.session.add(project)
            db.session.flush()

        db.session.commit()


def create_random_wav(filename, sr=11025, duration=2):
    x = np.random.rand(duration * sr) * 2 - 1
    wavio.write(filename, x, sr, sampwidth=2)
    

