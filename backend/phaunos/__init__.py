import click
from flask.cli import with_appcontext
from flask import Flask
from phaunos.phaunos.routes import phaunos_api
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import numpy as np
import wavio
import uuid
import os


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
    app.config.from_pyfile("config.py")
    
    if testing:
        app.config["TESTING"] = True

    initialize_extensions(app)
    app.register_blueprint(phaunos_api)
    register_cli(app)
    return app


def initialize_extensions(app):
    from phaunos.models import db, ma
    db.init_app(app)
    ma.init_app(app)
    migrate = Migrate(app, db)


################
## Custom CLI ##
################

def register_cli(app):

    @app.cli.command()
    def put_dummy_data():
        
        from phaunos.models import db
        from phaunos.phaunos.models import (
                Project,
                Tag,
                TagType,
                Audio,
                Annotation
                )
        from phaunos.user.models import User

        app.config["DUMMY_DATA_FOLDER"] = '/app/dummy_data'
        print(app.config["DUMMY_DATA_FOLDER"])
        print(app)

        n_tagtypes = 30
        n_tags = 5 # per tagtypes
        n_users = 10
        n_projects = 20
        n_audios = 100
        n_annotations = 1000

        # create users
        for i in range(n_users):
            user = User()
            user.name = f"user{i}"
            db.session.add(user)

        # create tagtypes
        for i in range(n_tagtypes):
            tagtype = TagType()
            tagtype.name = f"tagtype{i}"
            db.session.add(tagtype)
            db.session.flush()

            # create tags
            for j in range(n_tags):
                tag = Tag()
                tag.name = f"tag{i}_{j}"
                tag.tagtype_id = tagtype.id
                db.session.add(tag)
                db.session.flush()

        # create audios
        for i in range(n_audios):
            audio = Audio()
            audio.rel_path = create_random_wav(app.config['DUMMY_DATA_FOLDER'])
            db.session.add(audio)
            db.session.flush()

        db.session.commit()


def create_random_wav(outdir, sr=11025, duration=2):

    x = np.random.rand(duration * sr) * 2 - 1
    filename = str(uuid.uuid4()) + ".wav"
    wavio.write(os.path.join(outdir, filename), x, sr, sampwidth=2)
    return filename
    


