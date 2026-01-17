#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import paho.mqtt.client as mqtt

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from src.data_model.device import Device
from src.data_model.device import DeviceParams

from typing import Unpack
from typing import Dict
from typing import Any
from typing import Union


class ActuatorParams(DeviceParams):
    pass

class Actuator(Device):

    __mapper_args__ = {
        "polymorphic_identity": "actuator",
    }

    def __init__(self, **kwargs: Unpack[ActuatorParams]):
        super().__init__(**kwargs)
        self._online: Union[bool, None] = None
        self._state: Union[bool, None] = None
        self._pending_state: bool = False

    @property
    def online(self) -> Union[bool, None]:
        return self._online

    def on_online(self, data: Dict[str, Any]) -> None:
        online: str = data.get('state', None)
        if online is not None:
            self._online = online.upper() == 'ONLINE'

    def on_get(self, data: Dict[str, Any]) -> None:
        self._pending_state = False
        state: str = data.get('state', None)
        if state is not None:
            self._state = state.upper() == 'ON'

    @property
    def on(self) -> bool:
        return self._state

    @on.setter
    def on(self, value: bool) -> None:
        if not self._pending_state:
            if value:
                Device.publish_queue.put({'topic': self.friendly_name + '/set', 'payload': {'state': "ON"}})
            else:
                Device.publish_queue.put({'topic': self.friendly_name + '/set', 'payload': {'state': "OFF"}})
            Device.publish_queue.put({'topic': self.friendly_name + '/get', 'payload': {'state': ""}})
            self._pending_state = True

    @property
    def off(self) -> bool:
        return not self._state

    @off.setter
    def off(self, value: bool) -> None:
        if not self._pending_state:
            if value:
                Device.publish_queue.put({'topic': self.friendly_name + '/set', 'payload': {'state': "OFF"}})
            else:
                Device.publish_queue.put({'topic': self.friendly_name + '/set', 'payload': {'state': "ON"}})
            Device.publish_queue.put({'topic': self.friendly_name + '/get', 'payload': {'state': ""}})
            self._pending_state = True
