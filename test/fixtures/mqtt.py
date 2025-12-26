#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest

import json
from pathlib import Path

# Mapping of topics to their sample data files
TOPIC_FILE_MAP = {
    "base/bridge/devices": "base_bridge_devices.json",
    "sensors/humidity": "humidity_data.json",
    "alerts/system": "alert_payload.json"
}


@pytest.fixture
def mqtt_payload(request):
    """
    Loads a file based on a 'topic' key passed from the test.
    Expects request.param to be a string (the topic).
    """
    topic = request.param
    filename = TOPIC_FILE_MAP.get(topic)

    if not filename:
        raise ValueError(f"No payload file mapped for topic: {topic}")

    payload_path = Path(__file__).parent / "data" / filename

    with open(payload_path, "r") as f:
        return json.load(f)

