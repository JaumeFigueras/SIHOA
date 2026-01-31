#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import enum

class ControlledBy(enum.StrEnum):
    SUNSET_SUNRISE = 'SUNSET_SUNRISE'
    DUSK_DAWN = 'DUSK_DAWN'
    SUNSET_TIME = 'SUNSET_TIME'
    TIME_SUNRISE = 'TIME_SUNRISE'
    TIME = 'TIME'
    THRESHOLD = 'THRESHOLD'


class OverrideBy(enum.StrEnum):
    NONE = 'NONE'
    PUSH_BUTTON = 'PUSH_BUTTON'
