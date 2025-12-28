#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

test_folder: Path = Path(__file__).parent

pytest_plugins = [
    'test.fixtures.database',
    'test.fixtures.mqtt',
    'test.fixtures.mosquitto',
]
