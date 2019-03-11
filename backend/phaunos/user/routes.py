import datetime
from flask import (
    Blueprint,
    request,
    jsonify,
    url_for,
    render_template,
    redirect,
    current_app,
)
from flask_jwt_extended import create_refresh_token, create_access_token
from phaunos.shared import db
from phaunos.phaunos.models import user_schema
import re
from marshmallow import ValidationError
from werkzeug.security import check_password_hash
from .models import User
from ..email_utils import send_confirmation_email, generate_confirmation_token, confirm_token
from ..utils import build_response
from sqlalchemy import exc


user_api = Blueprint('user_api', __name__)


@user_api.route('/api/user/register', methods=('POST',))
def register():

    data = request.get_json()

    try:

        # Validate schema
        data = user_schema.load(data)

        # Create unconfirmed user if email is not already registered
        if User.query.filter(User.email == data['email']).first():
            return build_response(409, 'That email address is already in the database')
        user = User(data['username'],
            email=data['email'],
            password=data['password'],
        )
        user.save()

        # Send confirmation email
        token = generate_confirmation_token(user.email)
        send_confirmation_email(user.email, token)
        return build_response(
            201,
            f'Successfully created user: {user.email}. Please confirm email.')

    except ValidationError as err:
        return build_response(400, err.messages)
    
    except exc.SQLAlchemyError:
        return build_response(500, 'SQLAlchemy error.')


@user_api.route('/api/user/request_confirmation_email', methods=('POST',))
def request_confirmation_email():

    data = request.get_json()

    user = User.query.filter(User.email == data['email']).first()
    
    if not user:
        return build_response(400, f'{user.email} not found')

    if user.confirmed_on:
        return build_response(400, f'{user.email} already confirmed')

    token = generate_confirmation_token(user.email)
    send_confirmation_email(user.email, token)
    return build_response(200, f'A confirmation email has been sent to {user.email}')


@user_api.route('/api/user/confirm/<token>')
def confirm_email(token):

    try:
        email = confirm_token(token, current_app.config['CONFIRMATION_TOKEN_EXPIRATION'])
    except:
        return build_response(400, 'The confirmation link is invalid or has expired.')

    user = User.query.filter_by(email=email).first()
    if user.confirmed_on:
        return build_response(400, f'{user.email} already confirmed')
    else:
        user.confirmed_on = datetime.datetime.now()
        db.session.add(user)
        db.session.commit()
        return build_response(200, 'You have confirmed your account. Thank you!')
    return redirect(url_for('phaunos_api.home'))


@user_api.route('/api/user/login', methods=('POST',))
def login():

    data = request.get_json()
    user = User.query.filter(User.username==data['username']).first()

    if not user:
        return build_response(400, 'User {} doesn\'t exist'.format(data['username']))

    if not user.confirmed_on:
        return build_response(400, f'{user.email} not confirmed')

    if check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity = data['username'], fresh=True)
        refresh_token = create_refresh_token(identity = data['username'])
        return build_response(200,
                              f'Logged in as {user.username}',
                              {'access_token': access_token, 'refresh_token': refresh_token})
    else:
        return build_response(401, 'Invalid username or password.')


@user_api.route('/api/user/logout')
def logout():
    # just delete the token on the client
    pass
