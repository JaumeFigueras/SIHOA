#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse  # pragma: no cover
import sys  # pragma: no cover
import json  # pragma: no cover
import time  # pragma: no cover
import paho.mqtt.client as mqtt

from sqlalchemy import create_engine  # pragma: no cover
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from typing import Optional
from typing import Any


def read_zigbee2mqtt_devices(host: str, port: int, topic: str, timeout_s: float = 5.0, username: Optional[str]=None, password: Optional[str]=None, ) -> list[dict[str, Any]]:
    """Retrieve the Zigbee2MQTT device list from the retained devices topic.

    Parameters
    ----------
    host : str, optional
        MQTT broker hostname or IP. Default is 'localhost'.
    port : int, optional
        MQTT broker port. Default is 1883.
    username : str or None, optional
        Username for broker authentication, if required.
    password : str or None, optional
        Password for broker authentication, if required.
    topic : str, optional
        Zigbee2MQTT devices topic. Default is 'zigbee_network/bridge/devices'.
    timeout_s : float, optional
        Maximum time to wait for the retained message (seconds). Default is 5.0.

    Returns
    -------
    list of dict
        The list of device descriptors published by Zigbee2MQTT. Returns an
        empty list if no message is received within the timeout or parsing fails.
    """
    devices: list[dict[str, Any]] = list()

    def on_message(_client: mqtt.Client, _userdata: Any, msg: mqtt.MQTTMessage):
        if msg.topic != topic:
            return
        try:
            payload = (msg.payload or b"[]").decode("utf-8")
            data = json.loads(payload)
            if isinstance(data, list):
                nonlocal devices
                devices = data
        except Exception as xcpt:
            raise xcpt

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if username or password:
        client.username_pw_set(username=username or "", password=password or "")
    client.on_message = on_message

    # Connect and subscribe
    client.connect(host, port, keepalive=30)
    client.subscribe(topic, qos=0)

    # Start network loop and wait for retained message
    client.loop_start()
    try:
        start = time.time()
        while time.time() - start < timeout_s:
            if devices:
                break
            time.sleep(0.05)
    finally:
        client.loop_stop()
        try:
            client.disconnect()
        except Exception as xcpt:
            raise xcpt

    return devices

if __name__ == "__main__":  # pragma: no cover
    # Config the program arguments
    parser = argparse.ArgumentParser(description="Fetch Zigbee2MQTT device list from MQTT")
    parser.add_argument('-d', '--database', help='SQLite database file', required=False, default=None)
    parser.add_argument("-H", "--host", default="localhost", help="MQTT broker host (default: localhost)")
    parser.add_argument("-p", "--port", type=int, default=1883, help="MQTT broker port (default: 1883)")
    parser.add_argument("-u", "--username", default=None, help="MQTT username (optional)")
    parser.add_argument("-P", "--password", default=None, help="MQTT password (optional)")
    parser.add_argument("-t", "--topic", default="base_topic/bridge/devices", help="Zigbee2MQTT devices topic (default: <base_topic>/bridge/devices)")
    parser.add_argument("-w", "--timeout", type=float, default=5.0, help="Timeout for retained message (seconds)")
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

    try:
        devices_zigbee = read_zigbee2mqtt_devices(args.host, args.port, args.topic, args.timeout, username=args.username, password=args.password)
        print(json.dumps(devices_zigbee, ensure_ascii=False, indent=2))
        sys.exit(0)
    except Exception as xcpt:
        print(f"Error: {xcpt}", file=sys.stderr)
        sys.exit(-2)
