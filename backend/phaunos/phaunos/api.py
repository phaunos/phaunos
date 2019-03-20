from flask import (
    send_from_directory,
    current_app,
    make_response,
    Response,
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
    Annotation,
    project_schema,
    annotation_schema,
    tagset_schema,
#    tag_schema,
    audio_schema,
    user_schema
)

from phaunos.user.models import User

from flask_jwt_extended import (
    fresh_jwt_required,
    jwt_required,
    get_jwt_identity,
    get_current_user
)

from phaunos.shared import db, bp_api
from phaunos.utils import build_response



# get project (without audios and annotations) 
# all: /projects
# by id: /projects/<id> (only for project admins)

# get tagsets (with tags)
# /tagsets
# params:
#   project_id=<id> (required)

# get audios
# /audios
# params:
#   project_id=<id> (required) (only for project admins)

# get annotations
# /annotations (all if the user connected is project admin. Only those made by the user connected otherwise.)
# -filter by project: project_id=<id> (required)
#- filter by audio: audio_id=<id>
#- filter by user: user_id=<id>
#- filter by tag: tag_id=<id>

# get users
#- by id: /users/<id>
#- by project: /users?project_id=<id>


@bp_api.route('/')
def home():
    return 'Home'


@bp_api.route('/api/phaunos/users', methods=['GET'])
@jwt_required
def users():
    page = request.args.get('page', 1, type=int)
    user = get_current_user()
    project_id = request.args.get('project_id', None, type=int)
    if project_id:
        if not Project.query.get(project_id):
            return build_response(f'Project with id {project_id} not found'), 404
        if not (user.is_admin or user.is_project_admin(project_id)):
            return build_response('Not allowed.'), 403
        query = db.session.query(User).join(UserProjectRel) \
            .filter(UserProjectRel.project_id==project_id)
    elif not user.is_admin:
        return build_response('Not allowed.'), 403
    else:
        query = User.query
    return user_schema.dumps(query.paginate(page, 10, False).items, many=True)
    







@bp_api.route('/api/phaunos/projects', methods=['GET'])
#@jwt_required
def projects():
    page = request.args.get('page', 1, type=int)
    projects = Project.query.order_by(Project.name).paginate(page, 10, False)
    return project_schema.dumps(projects.items, many=True)


@bp_api.route('/api/phaunos/projects/<int:project_id>', methods=['GET'])
@jwt_required
def project_detail(project_id):
    user = get_current_user()
    project = Project.query.get(project_id)
    current_app.logger.info(user)
    current_app.logger.info(project)
    if not project:
        return build_response(f'Project with id {project_id} not found'), 404
    if not (user.is_admin or user.is_project_admin(project_id)):
        return build_response('Not allowed.'), 403
    return project_schema.dumps(project)


@bp_api.route('/api/phaunos/tagsets', methods=['GET'])
#@jwt_required
def tagsets():
    page = request.args.get('page', 1, type=int)
    project_id = request.args.get('project_id', None, type=int)

    # Filter by project (required)
    if not project_id:
        return build_response('Missing project_id parameter.'), 422
    if not Project.query.get(project_id):
        return build_response(f'Project with id {project_id} not found'), 404
    subquery = Tagset.query.filter(Tagset.projects.any(Project.id==project_id))

    return tagset_schema.dumps(
        subquery.paginate(page, 10, False).items,
        many=True)


@bp_api.route('/api/phaunos/audios', methods=['GET'])
@jwt_required
def audios():
    page = request.args.get('page', 1, type=int)
    user = get_current_user()
    project_id = request.args.get('project_id', None, type=int)

    # Filter by project (required)
    if not project_id:
        return build_response('Missing project_id parameter.'), 422
    if not Project.query.get(project_id):
        return build_response(f'Project with id {project_id} not found'), 404
    subquery = Audio.query.filter(Audio.projects.any(Project.id==project_id))

    # Check user is project admin
    if not (user.is_admin or user.is_project_admin(project_id)):
        return build_response('Not allowed.'), 403

    return audio_schema.dumps(
        subquery.paginate(page, 10, False).items,
        many=True)


@bp_api.route('/api/phaunos/annotations', methods=['GET'])
@jwt_required
def annotations():
    web = request.args.get('web', 0, type=int)
    page = request.args.get('page', 1, type=int)
    user = get_current_user()
    project_id = request.args.get('project_id', None, type=int)
    audio_id = request.args.get('audio_id', None, type=int)
    tag_id = request.args.get('tag_id', None, type=int)

    # Filter by project (required)
    if not project_id:
        return build_response('Missing project_id parameter.'), 422
    if not Project.query.get(project_id):
        return build_response(f'Project with id {project_id} not found'), 404
    subquery = Annotation.query.filter(Annotation.project_id==project_id)
    
    # Filter by audio
    if audio_id:
        if not Audio.query.get(audio_id):
            return build_response(f'Audio with id {audio_id} not found'), 404
        subquery = subquery.filter(Annotation.audio_id==audio_id)

    # Filter by tag
    if tag_id:
        if not Tag.query.get(tag_id):
            return build_response(f'Tag with id {tag_id} not found'), 404
        subquery = subquery.filter(Annotation.tag_id==tag_id)

    # If the user is not project admin, only get his annotations
    if not (user.is_admin or user.is_project_admin(project_id)):
        subquery = subquery.filter(Annotation.created_by_id==user.id)


    if web:
        data = subquery.all()
        return Response(
            data,
            mimetype='application/json',
            headers={'Content-Disposition':'attachment;filename=annotations.json'})
    else:
        data = subquery.paginate(page, 10, False).items
        return annotation_schema.dumps(data, many=True)


@bp_api.route('/files/<path:filename>')
def uploaded(filename):
    return send_from_directory('/app/files',
            filename)
