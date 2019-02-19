from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager

ma = Marshmallow()
db = SQLAlchemy()
jwt = JWTManager()
