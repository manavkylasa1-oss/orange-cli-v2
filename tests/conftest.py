from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pytest

from app import create_app
from app.config import TestConfig
from app.db import db
from app.models import Security, User


@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session."""
    app = create_app(TestConfig)
    
    with app.app_context():
        # Create all database tables
        db.create_all()
        yield app
        # Drop all database tables after session completes
        db.drop_all()


@pytest.fixture(scope='session')
def client(app):
    """A test client for the app."""
    return app.test_client()


from sqlalchemy.orm import scoped_session, sessionmaker

@pytest.fixture(scope='function')
def db_session(app, monkeypatch):
    """
    A fixture that creates a new database session for a test and rolls back
    any changes after the test completes, maintaining an isolated test state.
    """
    with app.app_context():
        # Start a transaction on the actual DB engine
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Bind the session to the connection
        session_factory = sessionmaker(bind=connection)
        session = scoped_session(session_factory)
        
        # Monkeypatch db.session to use this isolated local session
        # This ensures all calls to db.session in the app use our test session
        monkeypatch.setattr(db, 'session', session)
        
        # Populate initial test data
        _populate_database(session)

        yield session

        # Tidy up local session and rollback transaction
        session.remove()
        transaction.rollback()
        connection.close()


def _populate_database(session):
    try:
        admin_user = User(username='admin', password='admin', firstname='Admin', lastname='User', balance=1000.00)
        session.add(admin_user)

        securities = [
            Security(ticker='AAPL', issuer='Apple Inc.', price=150.00),
            Security(ticker='GOOGL', issuer='Alphabet Inc.', price=2800.00),
            Security(ticker='MSFT', issuer='Microsoft Corp.', price=300.00),
        ]
        session.add_all(securities)
        # We must flush to ensure the objects are available inside the transaction
        session.flush() 
    except Exception:
        session.rollback()
