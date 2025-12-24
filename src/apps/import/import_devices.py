#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse  # pragma: no cover
import sys  # pragma: no cover

from sqlalchemy import create_engine  # pragma: no cover
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def main(session: Session):
    pass

if __name__ == "__main__":  # pragma: no cover
    # Config the program arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', help='SQLite database file', required=False, default=None)
    args = parser.parse_args()

    try:
        if args.database is None:
            engine_db = create_engine("sqlite:///foo.db")
        else:
            engine_db = create_engine("sqlite:///" + args.database)
        session_db = Session(bind=engine_db)
    except SQLAlchemyError as ex:
        print(ex)
        sys.exit(-1)

    main(session_db)
