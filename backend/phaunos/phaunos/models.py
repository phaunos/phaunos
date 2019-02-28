import enum
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.event import listens_for
from sqlalchemy.dialects.postgresql import ENUM
from phaunos.shared import db, ma
from phaunos.user.models import User
from sqlalchemy.ext.declarative import declarative_base
from marshmallow import fields

Base = declarative_base()


@enum.unique
class VisualizationType(enum.Enum):
    WAVEFORM = enum.auto()
    SPECTROGRAM = enum.auto()

@enum.unique
class Role(enum.Enum):
    ADMIN = enum.auto()
    MEMBER = enum.auto()


audio_project_rel = db.Table('audio_project_rel',
        db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
        db.Column('audio_id', db.Integer, db.ForeignKey('audio.id'), primary_key=True)
        )

tagset_project_rel = db.Table('tagset_project_rel',
        db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
        db.Column('tagset_id', db.Integer, db.ForeignKey('tagset.id'), primary_key=True)
        )

tag_tagset_rel = db.Table('tag_tagset_rel',
        db.Column('tagset_id', db.Integer, db.ForeignKey('tagset.id'), primary_key=True),
        db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
        )


class UserProjectRel(db.Model):
    __tablename__ = 'user_project_rel'
    user_id = db.Column(db.Integer, db.ForeignKey('phaunos_user.id'), primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    user_role = db.Column(ENUM(Role), nullable=False)

    user = db.relationship('User', backref=db.backref('user_project_rel', cascade='all'))
    project = db.relationship('Project', backref=db.backref('user_project_rel', cascade='all'))


class Tag(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    annotations = db.relationship('Annotation',
            backref='tag',
            lazy=True,
            cascade='all')

    def __repr__(self):
        return '<name {}>'.format(self.name)

class Tagset(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    tags = db.relationship(
        'Tag',
        secondary=tag_tagset_rel,
        lazy=True,
        backref='tagsets'
    )

    def __repr__(self):
        return '<name {}>'.format(self.name)





class Audio(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    rel_path = db.Column(db.String, unique=True, nullable=False)
    annotations = db.relationship(
        'Annotation',
        backref='audio',
        cascade='all',
        lazy=True
    )

    def __repr__(self):
        return '<id {}>'.format(self.rel_path)

class Annotation(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Float, nullable=True)
    end_time = db.Column(db.Float, nullable=True)
    tag_id = db.Column(db.Integer, db.ForeignKey(Tag.id), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    audio_id = db.Column(db.Integer, db.ForeignKey('audio.id'), nullable=False)
    user_id  = db.Column(db.Integer, db.ForeignKey('phaunos_user.id'), nullable=False)
    user = db.relationship(User, backref=db.backref('annotations', cascade='all'))

    def __repr__(self):
        return '<id {}>'.format(self.id)



class Project(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    audio_root_url = db.Column(db.String, nullable=False)
    visualization_type = db.Column(ENUM(VisualizationType), default=VisualizationType.SPECTROGRAM, nullable=False)
    allow_regions = db.Column(db.Boolean, nullable=False)
    n_annotations_per_file = db.Column(db.Integer, nullable=True)
    tagsets = db.relationship('Tagset',
            secondary=tagset_project_rel,
            lazy=True,
            backref=db.backref('projects', lazy=True))
    audios = db.relationship('Audio',
            secondary=audio_project_rel,
            lazy=True,
            backref=db.backref('projects', lazy=True))
    annotations = db.relationship(
        'Annotation',
        lazy=True,
        cascade='all',
        backref='project'
    )
    audios_filename = db.Column(db.String, nullable=True)
    annotations_filename = db.Column(db.String, nullable=True)

    @property
    def is_completed(self):
        if (self.n_annotations_per_file and
                self.annotations.count() >= self.audios.count() * self.n_annotations_per_file):
            return True
        return False

    def __repr__(self):
        return '<name {}>'.format(self.name)


class EnumField(fields.Field):

    def __init__(self, enumtype, *args, **kwargs):
        super(EnumField, self).__init__(*args, **kwargs)
        self._enumtype = enumtype

    def _serialize(self, value, attr, obj, **kwargs):
        return value.name

    def _deserialize(self, value, attr, data, **kwargs):
        return self._enumtype[value]


class ProjectSchema(ma.ModelSchema):
    visualization_type = EnumField(VisualizationType)
    class Meta:
        model = Project
        exclude = (
            'tagsets',
            'audios',
            'annotations',
            'user_project_rel')
project_schema = ProjectSchema()


class TagSchema(ma.ModelSchema):
    class Meta:
        model = Tag
        exclude = ('annotations', 'tagsets')
#tag_schema = TagSchema()


class TagsetSchema(ma.ModelSchema):
    class Meta:
        model = Tagset
        exclude = ('projects',)
    tags = ma.Nested(TagSchema, many=True)
tagset_schema = TagsetSchema()


class AudioSchema(ma.ModelSchema):
    class Meta:
        model = Audio
        exclude = ('projects', 'annotations')

audio_schema = AudioSchema()


class AnnotationSchema(ma.ModelSchema):
    class Meta:
        model = Annotation

annotation_schema = AnnotationSchema()



#@listens_for(Project, 'after_delete')
#def del_file(mapper, connection, target):
#    if target.audios_filename:
#        try:
#            os.remove(os.path.join(app.config['UPLOAD_DIR'], 'audios', target.audios_filename))
#        except OSError:
#            # Don't care if was not deleted because it does not exist
#            pass
#    if target.annotations_filename:
#        try:
#            os.remove(os.path.join(app.config['UPLOAD_DIR'], 'annotations', target.annotations_filename))
#        except OSError:
#            # Don't care if was not deleted because it does not exist
#            pass
#
#
