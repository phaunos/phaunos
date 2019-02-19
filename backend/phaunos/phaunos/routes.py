from flask import (
    Blueprint,
    send_from_directory,
    current_app,
    make_response,
    request,
    render_template,
    jsonify
)
from phaunos.phaunos.models import (
    Audio,
    Tag,
    Tagset,
    Project,
    Role,
    VisualizationType,
    UserProjectRel,
    project_schema,
    tagset_schema,
#    tag_schema,
    audio_schema,
)


from flask_jwt_extended import (
    fresh_jwt_required,
    jwt_required,
    get_jwt_identity,
    get_current_user
)

from phaunos.shared import db
from phaunos.utils import build_response



phaunos_api = Blueprint('phaunos_api', __name__)


# get project (without audios and annotations) 
#+ all: /projects (pagination)
#+ by id: /projects/<id> (only for admins)

# get tagsets (with tags)
#+ by project: /tagsets?project_id=<id>

# get audios
#+ by project: /audios?project_id=<id> (pagination) (only for admins)

# get annotations
#- by audio: /annotations?audio_id=<id> (pagination)
#- by user: /annotations?user_id=<id> (pagination)
#- by tag: /annotations?tag_id=<id> (pagination)

# get users
#- by id: /users/<id>
#- by project: /users?project_id=<id> (pagination)

@phaunos_api.route('/')
def home():
    return 'Home'


@phaunos_api.route('/api/phaunos/projects', methods=['GET'])
#@jwt_required
def projects():
    page = request.args.get('page', 1, type=int)
    projects = Project.query.order_by(Project.name).paginate(page, 10, False)
    return project_schema.dumps(projects.items, many=True)


@phaunos_api.route('/api/phaunos/projects/<int:id>', methods=['GET'])
@jwt_required
def project_detail(id):
    user = get_current_user()
    project = Project.query.get(id)
    if not project:
        return build_response(404, 'Project not found')
    if not UserProjectRel.query.filter(
            UserProjectRel.project_id==id,
            UserProjectRel.user_id==user.id,
            UserProjectRel.user_role==Role.ADMIN).first():
        return build_response(403, 'Not allowed.')
    return project_schema.dumps(project)


@phaunos_api.route('/api/phaunos/tagsets', methods=['GET'])
#@jwt_required
def tagsets():
    page = request.args.get('page', 1, type=int)
    project_id = request.args.get('project_id', None, type=int)
    if project_id == None:
        return build_response(404, 'Project not found')
    tagsets = Tagset.query.filter(Tagset.projects.any(Project.id==project_id)).paginate(page, 10, False)
    return tagset_schema.dumps(tagsets.items, many=True)


@phaunos_api.route('/api/phaunos/audios', methods=['GET'])
@jwt_required
def audios():
    user = get_current_user()
    project_id = request.args.get('project_id', None, type=int)
    if project_id == None:
        return build_response(404, 'Project not found')
    if not UserProjectRel.query.filter(
            UserProjectRel.project_id==project_id,
            UserProjectRel.user_id==user.id,
            UserProjectRel.user_role==Role.ADMIN).first():
        return build_response(403, 'Not allowed.')
    page = request.args.get('page', 1, type=int)
    audios = Audio.query.filter(Audio.projects.any(Project.id==project_id)).paginate(page, 10, False)
    return audio_schema.dumps(audios.items, many=True)



@phaunos_api.route('/files/<path:filename>')
def uploaded(filename):
    return send_from_directory('/app/files',
            filename)
