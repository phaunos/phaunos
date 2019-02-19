from flask import current_app
from phaunos.shared import db, ma
from werkzeug.security import generate_password_hash
from marshmallow import Schema, fields, validate, pre_load, post_dump
from phaunos.shared import jwt



class User(db.Model):  
    __tablename__ = 'phaunos_user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = generate_password_hash(password, method='sha256')

    def save(self):
        db.session.add(self)
        db.session.commit()

    def to_dict(self):
        return dict(username=self.username, email=self.email)


class UserSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(
        required=True,
        validate=[validate.Length(min=4, max=20)],
    )
    email = fields.Str(
        required=True,
        validate=validate.Email(error='Not a valid email address'),
    )
    password = fields.Str(
        required=True,
        validate=[validate.Length(min=6, max=36)],
        load_only=True,
    )

    # Clean up data
    @pre_load
    def process_input(self, data):
        data['email'] = data['email'].lower().strip()
        return data

    # We add a post_dump hook to add an envelope to responses
#    @post_dump(pass_many=True)
#    def wrap(self, data, many):
#        key = 'users' if many else 'user'
#        return {
#            key: data,
#        }


user_schema = UserSchema()



@jwt.user_loader_callback_loader
def user_loader_callback(identity):
    user = User.query.filter(User.username==identity).first()
    if not user:
        return None
    return user
