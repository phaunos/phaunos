from flask import Blueprint
from flask import send_from_directory
from flask import current_app
#from phaunos.phaunos.models import Annotation, Audio, Project, Tag, TagType, VisualizationType
from phaunos.phaunos.models import (
        Audio,
        Tag,
        TagType,
        VisualizationType,
        tagtype_schema,
        tagtypes_schema,
        tag_schema,
        tags_schema,
        )


phaunos_api = Blueprint('phaunos_api', __name__)



# get project (without audios and annotations)
#- all: /projects (pagination)
#- by id: /projects/<id>

# get tagtypes (with tags)
#- by project: /tagtypes?project_id=<id>

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



@phaunos_api.route('/api/phaunos/tagtypes', methods=['GET'])
def tagtypes():
    return tagtypes_schema.jsonify(TagType.query.all())

@phaunos_api.route('/api/phaunos/tagtypes/<id>', methods=['GET'])
def tagtype_detail(id):
    tagtype = TagType.query.get(id)
    return tagtype_schema.jsonify(tagtype)


@phaunos_api.route('/api/phaunos/tags')
def tags():
    return tags_schema.jsonify(Tag.query.all())

@phaunos_api.route('/api/phaunos/tags/<id>')
def tag_detail(id):
    tag = Tag.query.get(id)
    return tag_schema.jsonify(tag)


@phaunos_api.route('/audio/<filename>')
def audio_file(filename):
    return send_from_directory('/app/dummy_data',
            filename)
