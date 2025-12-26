#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.data_model import Base

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Initialize schema once for the whole session
    with engine.connect() as connection:
        # Example of executing the script (as shown in previous step)
        # connection.execute(text("CREATE TABLE..."))
        # Or if using Declarative only:
        Base.metadata.create_all(connection)
        connection.commit()

    return engine

@pytest.fixture(scope="function")
def db_session(engine):
    """
    Creates a new session for a test, wrapped in a transaction
    that is always rolled back.
    """
    # 1. Connect to the database
    connection = engine.connect()

    # 2. Begin an outer transaction
    transaction = connection.begin()

    # 3. Bind the session to the connection
    # join_transaction_mode="create_savepoint" ensures that session.commit()
    # inside your code only ends a SAVEPOINT, not the real transaction.
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    # 4. Teardown: Roll back everything (including internal commits)
    session.close()
    transaction.rollback()
    connection.close()