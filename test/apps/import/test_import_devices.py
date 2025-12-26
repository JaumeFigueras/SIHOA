#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest


@pytest.mark.parametrize("mqtt_payload", ["base/bridge/devices"], indirect=True)
def test_read_zigbee2mqtt_devices(mqtt_payload):
    pass