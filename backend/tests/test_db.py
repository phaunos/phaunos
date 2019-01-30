import pytest
from phaunos import create_app
from phaunos.models import db
from phaunos.phaunos.models import TagType


@pytest.fixture(scope='module')
def test_app():
    app = create_app(testing=True)
    with app.app_context():
        yield app


@pytest.fixture(scope='module')
def test_db(test_app):
    db.drop_all()
    db.create_all()
    yield db
    db.session.remove()
    db.drop_all()


def test_add_tagtype(test_db):
    tt = TagType()
    tt.name = "tagtype1"
    db.session.add(tt)
    db.session.commit()
    assert len(TagType.query.all()) == 1

    
