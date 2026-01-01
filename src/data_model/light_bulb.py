#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from src.data_model.actuator import Actuator
from src.data_model.actuator import ActuatorParams

class LightBulbParams(ActuatorParams):
    pass

class LightBulb(Actuator):

    __mapper_args__ = {
        "polymorphic_identity": "light_bulb",
    }