#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy.orm import DeclarativeBase

# Creation of a declarative base for the SQL Alchemy models to inherit from
class Base(DeclarativeBase):
    """
    Declarative base class for SQLAlchemy models.

    This class serves as the base for all ORM models in the application.
    It is created using SQLAlchemy's ``DeclarativeBase`` to enable
    declarative mapping of Python classes to database tables.

    Notes
    -----
    All model classes should inherit from ``Base`` to automatically
    register them with SQLAlchemy's ORM and to define their corresponding
    table structure.

    See Also
    --------
    SQLAlchemy Declarative Mapping Documentation :
        `<https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html>`_
    """

    @staticmethod
    def is_defined_in_parents(cls, attr):
        return any(attr in base.__dict__ for base in cls.__bases__)
