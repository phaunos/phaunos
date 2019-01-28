import click
from flask.cli import with_appcontext
from flask import Flask
from phaunos.phaunos.routes import phaunos_api
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


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

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile("config.py")
    initialize_extensions(app)
    app.register_blueprint(phaunos_api)
    register_cli(app)
    return app


def initialize_extensions(app):
    # Since the application instance is now created, pass it to each Flask
    # extension instance to bind it to the Flask application instance (app)
    from phaunos.models import db, ma
    db.init_app(app)
    ma.init_app(app)
    migrate = Migrate(app, db)


################
## Custom CLI ##
################

def register_cli(app):

    @app.cli.command()
    def dummy():
        
        from phaunos.models import db
        from phaunos.phaunos.models import (
                Project,
                Tag,
                TagType,
                Audio,
                Annotation
                )
        from phaunos.user.models import User


        n_tagtypes = 3
        n_tags = 5 # per tagtypes
        n_users = 5
        n_projects = 3
        n_audios = 20
        n_annotations = 10

        # create users
        for i in n_users:
            user = User()
            user.name = f"user{i}"
            db.session.add(user)

        # create tagtypes
        for i in n_tagtypes:
            tagtype = TagType()
            tagtype.name = f"tagtype{i}"
            db.session.add(tagtype)
            db.session.flush()

            # create tags
            for j in n_tags:
                tag = Tag()
                tag.name = f"tag{i}_{j}"
                tag.tagtype_id = tagtype.id
                db.session.add(tag)






        
