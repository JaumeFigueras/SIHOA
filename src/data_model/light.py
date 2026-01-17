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

class LightParams(ActuatorParams):
    default_brightness: NotRequired[Union[int, None]]
    default_color_temp: NotRequired[Union[int, None]]
    default_power_on_behavior: NotRequired[Union[str, None]]

class Light(Actuator):

    __mapper_args__ = {
        "polymorphic_identity": "light",
    }

    def __init__(self, **kwargs: Unpack[LightParams]) -> None:
        super().__init__(**kwargs)
        self._brightness: Union[int, None] = None
        self._default_brightness: Union[int, None] = None
        self._color_mode: Union[str, None] = None
        self._color_temp: Union[int, None] = None
        self._default_color_temp: Union[int, None] = None
        self._link_quality: Union[int, None] = None
        self._power_on_behavior: Union[str, None] = None
        self._default_power_on_behavior: Union[str, None] = None
        self._color_temp_startup: Union[int, None] = None

    def on_online(self, data: Dict[str, Any]) -> None:
        super().on_online(data)
        if self._online:
            Device.publish_queue.put({'topic': self.friendly_name + '/get', 'payload': {'power_on_behavior': '', 'color_temp_startup': ''}})

    def on_get(self, data: Dict[str, Any]) -> None:
        super().on_get(data)
        brightness: str = data.get('brightness', None)
        color_mode: str = data.get('color_mode', None)
        color_temp: str = data.get('color_temp', None)
        link_quality: str = data.get('linkquality', None)
        power_on_behavior: str = data.get('power_on_behavior', None)
        color_temp_startup: str = data.get('color_temp_startup', None)
        if brightness is not None:
            self._brightness = int(brightness)
        if color_mode is not None:
            self._color_mode = color_mode
        if color_temp is not None:
            self._color_temp = int(color_temp)
        if link_quality is not None:
            self._link_quality = int(link_quality)
        if power_on_behavior is not None:
            self._power_on_behavior = power_on_behavior
        if color_temp_startup is not None:
            self._color_temp_startup = int(color_temp_startup)

    @Actuator.on.setter
    def on(self, value: bool) -> None:
        if not self._pending_state:
            if value:
                Device.publish_queue.put({'topic': self.friendly_name + '/set', 'payload': {'state': "ON", "transition": 0}})
            else:
                Device.publish_queue.put({'topic': self.friendly_name + '/set', 'payload': {'state': "OFF", "transition": 0}})
            Device.publish_queue.put({'topic': self.friendly_name + '/get', 'payload': {'state': ""}})
            self._pending_state = True

    @Actuator.off.setter
    def off(self, value: bool) -> None:
        if not self._pending_state:
            if value:
                Device.publish_queue.put({'topic': self.friendly_name + '/set', 'payload': {'state': "OFF", "transition": 0}})
            else:
                Device.publish_queue.put({'topic': self.friendly_name + '/set', 'payload': {'state': "ON", "transition": 0}})
            Device.publish_queue.put({'topic': self.friendly_name + '/get', 'payload': {'state': ""}})
            self._pending_state = True
