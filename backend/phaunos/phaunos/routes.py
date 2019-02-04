from flask import (
    Blueprint,
    send_from_directory,
    current_app,
    make_response,
    request,
    jsonify
)
from phaunos.phaunos.models import (
        Audio,
        Tag,
        Tagset,
        Project,
        VisualizationType,
        tagset_schema,
        tagsets_schema,
        tag_schema,
        tags_schema,
        )

from phaunos.models import db


phaunos_api = Blueprint('phaunos_api', __name__)



# get project (without audios and annotations)
#- all: /projects (pagination)
#- by id: /projects/<id>

# get tagsets (with tags)
#- by project: /tagsets?project_id=<id>

# get audios
#- by id: /audios/<id>
#- by project: /audios?project_id=<id> (pagination)

# get annotations
#- by audio: /annotations?audio_id=<id> (pagination)
#- by user: /annotations?user_id=<id> (pagination)
#- by tag: /annotations?tag_id=<id> (pagination)

# get users
#- by id: /users/<id>
#- by project: /users?project_id=<id> (pagination)



@phaunos_api.route('/api/phaunos/tagsets', methods=['GET'])
def tagsets():
    page = request.args.get('page', 1, type=int)
    project_id = request.args.get('project_id', None, type=int)
    if project_id == None:
        return make_response(jsonify({'error': 'Not found'}), 404)
    tagsets = Tagset.query.filter(Tagset.projects.any(Project.id==project_id))
    return tagsets_schema.jsonify(tagsets)

@phaunos_api.route('/api/phaunos/tagsets/<id>', methods=['GET'])
def tagset_detail(id):
    tagset = Tagset.query.get(id)
    return tagset_schema.jsonify(tagset)


@phaunos_api.route('/api/phaunos/tags')
def tags():
    page = request.args.get('page', 1, type=int)
    tags = Tag.query.paginate(
        page, 10, False)
    return tags_schema.jsonify(tags.items)

@phaunos_api.route('/api/phaunos/tags/<id>')
def tag_detail(id):
    tag = Tag.query.get(id)
    return tag_schema.jsonify(tag)


@phaunos_api.route('/files/<path:filename>')
def uploaded(filename):
    return send_from_directory('/app/files',
            filename)
