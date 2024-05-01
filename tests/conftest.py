import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base


@pytest.fixture(scope="session")
def engine():
    # Create an in-memory SQLite database
    return create_engine('sqlite:///:memory:')


@pytest.fixture(scope="session")
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="session")
def db_session(engine, tables):
    """Creates a session for interacting with the test database."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=engine)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
