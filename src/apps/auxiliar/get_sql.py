#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utility script for inspecting and printing SQLAlchemy ORM table definitions.

This script connects to a PostgreSQL database using SQLAlchemy and prints
the SQL statements for creating ORM-mapped tables. It is primarily used for
debugging and verifying schema generation of the project's data models.

Usage
-----
Run from the command line with the required connection arguments:

.. code-block:: bash

    python3 get_sql.py --host localhost --port 5432 --database testdb --username user --password pass

Named Arguments
---------------
| :code:`-H, --host`: Hostname of the PostgreSQL database cluster.
| :code:`-p, --port`: Port number of the PostgreSQL database cluster.
| :code:`-d, --database`: Name of the target database.
| :code:`-u, --username`: Database username for authentication.
| :code:`-w, --password`: Password for authentication.

""" # noinspection GrammarInspection

import argparse  # pragma: no cover
import sys  # pragma: no cover

from sqlalchemy import create_engine  # pragma: no cover
from sqlalchemy import URL  # pragma: no cover
from sqlalchemy import Engine  # pragma: no cover
from sqlalchemy.exc import SQLAlchemyError  # pragma: no cover
from sqlalchemy.schema import CreateTable  # pragma: no cover

from src.data_model import Base  # pragma: no cover
from src.data_model.device import Device

def main(e: Engine):  # pragma: no cover
    """
    Print SQLAlchemy table metadata and CREATE TABLE statements.

    Parameters
    ----------
    e : Engine
        A SQLAlchemy Engine connected to the target PostgreSQL database.

    Notes
    -----
    - Prints the list of all registered tables from `Base.metadata`.
    - Prints the CREATE TABLE SQL for `DataProvider` and `Lightning` tables.
    - Additional tables may be enabled by uncommenting their respective lines.
    """
    print(Base.metadata.tables.keys())
    # Base.metadata.create_all(e)
    print(CreateTable(Device.__table__).compile(e))

if __name__ == "__main__":  # pragma: no cover
    # Config the program arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', help='SQLite database file', required=False, default=None)
    args = parser.parse_args()

    try:
        if args.database is None:
            engine = create_engine("sqlite:///foo.db")
        else:
            engine = create_engine("sqlite:///" + args.database)
    except SQLAlchemyError as ex:
        print(ex)
        sys.exit(-1)

    main(engine)
