from flask import Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager


ma = Marshmallow()
db = SQLAlchemy()
jwt = JWTManager()

bp_api = Blueprint('bp_api', __name__)
bp_admin_auth = Blueprint('bp_admin_auth', __name__)


