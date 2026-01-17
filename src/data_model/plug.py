#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from src.data_model.device import Device
from src.data_model.actuator import Actuator
from src.data_model.actuator import ActuatorParams

from typing import Unpack, NotRequired
from typing import Union
from typing import Dict
from typing import Any

class PlugParams(ActuatorParams):
    pass

class Plug(Actuator):

    __mapper_args__ = {
        "polymorphic_identity": "plug",
    }

    def __init__(self, **kwargs: Unpack[PlugParams]) -> None:
        super().__init__(**kwargs)

    def on_online(self, data: Dict[str, Any]) -> None:
        super().on_online(data)
        if self._online:
            Device.publish_queue.put({'topic': self.friendly_name + '/get', 'payload': {'state': ''}})

    def on_get(self, data: Dict[str, Any]) -> None:
        super().on_get(data)

