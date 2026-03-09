import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pytest  # noqa: E402

from app import create_app  # noqa: E402
from app.config import TestConfig  # noqa: E402
from app.db import db  # noqa: E402
from app.models import Portfolio, User  # noqa: E402


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    app.config.update(TESTING=True)
    with app.app_context():
        db.create_all()
        owner = User(username='owner', password='x', firstname='Own', lastname='Er', balance=10000)
        viewer = User(username='viewer', password='x', firstname='View', lastname='Er', balance=1000)
        manager = User(username='manager', password='x', firstname='Manage', lastname='R', balance=1000)
        outsider = User(username='outsider', password='x', firstname='Out', lastname='Sider', balance=1000)
        db.session.add_all([owner, viewer, manager, outsider])
        db.session.flush()
        p = Portfolio(name='Main', description='Owner portfolio', owner='owner')
        db.session.add(p)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def mock_auth(monkeypatch):
    from app.auth import auth

    def _validate(token):
        if token == 'valid-owner':
            return {'sub': 'owner'}
        if token == 'valid-viewer':
            return {'sub': 'viewer'}
        if token == 'valid-manager':
            return {'sub': 'manager'}
        if token == 'valid-outsider':
            return {'sub': 'outsider'}
        raise Exception('invalid')

    monkeypatch.setattr(auth, 'validate_token', _validate)


def auth_header(token='valid-owner'):
    return {'Authorization': f'Bearer {token}'}
