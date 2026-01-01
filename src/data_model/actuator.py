#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations


from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from src.data_model.device import Device
from src.data_model.device import DeviceParams

from typing import Unpack


class ActuatorParams(DeviceParams):
    pass

class Actuator(Device):

    __mapper_args__ = {
        "polymorphic_identity": "actuator",
    }

    def __init__(self, **kwargs: Unpack[ActuatorParams]):
        super().__init__(**kwargs)


