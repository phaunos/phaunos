from phaunos.models import db, ma


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    def __repr__(self):
        return '<name {}>'.format(self.name)
