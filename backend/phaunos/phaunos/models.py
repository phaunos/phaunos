import enum
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.event import listens_for
from sqlalchemy.dialects.postgresql import ENUM
from phaunos.models import db, ma
from phaunos.user.models import User


@enum.unique
class VisualizationType(enum.Enum):
    WAVEFORM = enum.auto()
    SPECTROGRAM = enum.auto()

class TagType(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    tags = db.relationship('Tag',
            backref='tagtype',
            lazy=True,
            cascade='all')

    def __repr__(self):
        return '<name {}>'.format(self.name)


class Tag(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    tagtype_id = db.Column(db.Integer, db.ForeignKey(TagType.id), nullable=False)
    name = db.Column(db.String, nullable=False)
    annotations = db.relationship('Annotation',
            backref='tag',
            lazy=True,
            cascade='all')
    __table_args__ = (UniqueConstraint('name', 'tagtype_id'),)

    def __repr__(self):
        return '<name {}>'.format(self.name)


class Audio(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    rel_path = db.Column(db.String, unique=True, nullable=False)
    annotations = db.relationship('Annotation',
            backref='audio',
            lazy=True,
            cascade='all')

    def __repr__(self):
        return '<id {}>'.format(self.rel_path)

audio_project_rel = db.Table('audio_project_rel',
        db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
        db.Column('audio_id', db.Integer, db.ForeignKey('audio.id'), primary_key=True)
        )


tag_project_rel = db.Table('tag_project_rel',
        db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
        db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
        )


class Annotation(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Float, nullable=True)
    end_time = db.Column(db.Float, nullable=True)
    tag_id = db.Column(db.Integer, db.ForeignKey(Tag.id), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    audio_id = db.Column(db.Integer, db.ForeignKey('audio.id'), nullable=False)
    user_id  = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return '<id {}>'.format(self.id)


class Project(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    audio_root_url = db.Column(db.String, nullable=False)
    visualization_type = db.Column(ENUM(VisualizationType), default=VisualizationType.SPECTROGRAM, nullable=False)
    allow_regions = db.Column(db.Boolean, nullable=False)
    n_annotations_per_file = db.Column(db.Integer, nullable=True)
    tags = db.relationship('Tag',
            secondary=tag_project_rel,
            lazy=True,
            backref=db.backref('projects', lazy=True))
    audios = db.relationship('Audio',
            secondary=audio_project_rel,
            lazy=True,
            backref=db.backref('projects', lazy=True))
    annotations = db.relationship('Annotation',
            backref='project',
            lazy=True,
            cascade='all')
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


class TagSchema(ma.ModelSchema):
    class Meta:
        model = Tag

tag_schema = TagSchema(strict=True)
tags_schema = TagSchema(many=True, strict=True)


class TagTypeSchema(ma.ModelSchema):
    class Meta:
        strict = True
        model = TagType
    tags = ma.Nested(TagSchema, many=True)

tagtype_schema = TagTypeSchema(strict=True)
tagtypes_schema = TagTypeSchema(many=True, strict=True)


class AudioSchema(ma.ModelSchema):
    class Meta:
        strict = True
        model = Audio

audio_schema = AudioSchema(strict=True)
audios_schema = AudioSchema(many=True, strict=True)


class AnnotationSchema(ma.ModelSchema):
    class Meta:
        strict = True
        model = Annotation

annotation_schema = AnnotationSchema(strict=True)
annotation_schema = AnnotationSchema(many=True, strict=True)




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
