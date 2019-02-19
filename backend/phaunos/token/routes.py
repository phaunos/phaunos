from flask import (
    Blueprint,
    jsonify,
)

from flask_jwt_extended import (
    jwt_refresh_token_required,
    get_jwt_identity,
    create_access_token
)



token_api = Blueprint('token_api', __name__)


# Refresh token endpoint. This will generate a new access token from
# the refresh token, but will mark that access token as non-fresh,
# as we do not actually verify a password in this endpoint.
@token_api.route('/api/token/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user, fresh=False)
    ret = {'access_token': new_token}
    return jsonify(ret), 200
