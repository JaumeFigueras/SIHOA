#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Import Zigbee devices from Zigbee2MQTT via MQTT.

This program subscribes to the Zigbee2MQTT retained devices topic and prints
the device list as JSON. Your Zigbee2MQTT base topic is generalized to
``zigbee_network``, so the devices list should be available at:
``zigbee_network/bridge/devices``.

Notes
-----
- Zigbee2MQTT publishes a retained JSON array of device descriptors to
  ``<base_topic>/bridge/devices``. Subscribing to this topic should immediately
  return the current list if retention is enabled (default).
- Broker authentication (username/password) is optional and depends on your
  Mosquitto setup; admin privileges are not required for reading this topic.
- This module provides a single function `read_zigbee2mqtt_devices` and a simple
  CLI that calls it directly. No `main(session)` function is used.

Examples
--------
$ python -m src.apps.import.import_devices --host localhost --port 1883 \\
    --topic zigbee_network/bridge/devices
"""


import argparse
import sys
import json
import time
import datetime
import dateutil
import paho.mqtt.client as mqtt

from datetime import timezone
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.data_model.device import Device

from typing import Optional
from typing import Any
from typing import Tuple


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


def _parse_date_maybe(value: Any) -> Optional[datetime.date]:
    """Parse a date-like value to `date` using python-dateutil.

    Parameters
    ----------
    value : Any
        Raw value (string/date/datetime) potentially representing a date.

    Returns
    -------
    date or None
        Parsed date if recognized; otherwise None.
    """
    if value is None:
        return None
    if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        return value
    if isinstance(value, datetime.datetime):
        return value.date()
    # Only attempt to parse strings; ignore other types (e.g., int/float/objects)
    if not isinstance(value, str):
        return None

    try:
        return dateutil.parser.parse(value.strip()).date()
    except Exception:
        return None


def store_devices_to_db(session: Session, devices: list[dict[str, Any]]) -> Tuple[int, int]:
    """Upsert devices and retire missing ones using the SQLAlchemy `Device` model.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
        An active SQLAlchemy session bound to the target SQLite database.
    devices : list of dict
        Device descriptors as provided by Zigbee2MQTT (from '<base>/bridge/devices').

    Returns
    -------
    int, int
        Number of devices processed (created/updated) and umber of devices retired.

    Behavior
    --------
    - Uses `ieee_address` as the primary key. If a device with the same IEEE
      address exists, its attributes are updated; otherwise, a new row is created.
    - For devices present in the retained list, ensures `retired_at` is cleared (set to None).
    - Devices present in the database but missing from the retained list are marked
      retired by setting `retired_at` to the current UTC timestamp.
    - Fields mapped:
        * ieee_address            <- 'ieee_address' | 'ieeeAddress' | 'ieee'
        * friendly_name           <- 'friendly_name' | 'friendlyName' | 'name'
        * network_address         <- 'network_address' | 'networkAddress' (int)
        * device_type             <- 'type' | 'device_type'
        * zigbee_model            <- 'model' | 'zigbee_model'
        * zigbee_manufacturer     <- 'manufacturer' | 'zigbee_manufacturer'
        * firmware_version        <- 'software_version' | 'firmware_version'
        * firmware_build_date     <- 'software_build_id' | 'firmware_build_date' | 'date_code' (parsed)
    - Commits once after processing the entire list and retirements.
    """
    processed_count = 0

    # Track active IEEE addresses from the retained device list
    active_ieee: set[str] = set()

    # Upsert current devices and clear retired_at for active entries
    for d in devices:
        if not isinstance(d, dict):
            continue

        friendly_name = d.get("friendly_name") or d.get("friendlyName") or d.get("name")
        ieee_address = d.get("ieee_address") or d.get("ieeeAddress") or d.get("ieee")

        # Skip entries missing essential identifiers.
        if not ieee_address or not friendly_name:
            continue
        # Fetch existing device by primary key (ieee_address)
        device = session.get(Device, ieee_address)
        if device is None:
            device = Device(ieee_address=ieee_address, friendly_name=friendly_name)
            session.add(device)
        else:
            # Ensure friendly name stays in sync if it changed
            device.friendly_name = friendly_name
        active_ieee.add(ieee_address)

        # Optional fields
        net_addr = d.get("network_address") or d.get("networkAddress")
        try:
            device.network_address = int(net_addr) if net_addr is not None else None
        except Exception as xcpt:
            # Keep previous value if conversion fails
            pass

        device.device_type = (d.get("type") or d.get("device_type")) or device.device_type
        device.zigbee_model = (d.get("model") or d.get("zigbee_model")) or device.zigbee_model
        device.zigbee_manufacturer = (d.get("manufacturer") or d.get("zigbee_manufacturer")) or device.zigbee_manufacturer
        device.firmware_version = (d.get("software_version") or d.get("firmware_version")) or device.firmware_version

        build_raw = d.get("software_build_id") or d.get("firmware_build_date") or d.get("date_code")
        parsed_build_date = _parse_date_maybe(build_raw)
        if parsed_build_date is not None:
            device.firmware_build_date = parsed_build_date

        # An active device should not be retired
        device.retired_at = None

        processed_count += 1

    # Retire devices missing from the retained list:
    # Only consider devices that are not already retired (retired_at IS NULL)
    retired_count = 0
    for existing in session.scalars(select(Device).where(Device.retired_at.is_(None))).all():
        if existing.ieee_address not in active_ieee:
            existing.retired_at = datetime.datetime.now(timezone.utc)
            retired_count += 1

    # Persist all changes in a single transaction
    session.commit()
    return processed_count, retired_count


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
        processed, retired = store_devices_to_db(session_db, devices_zigbee)
        print(f"Stored/updated {processed} devices. Retired {retired} devices", file=sys.stderr)
        sys.exit(0)
    except Exception as xcpt:
        print(f"Error: {xcpt}", file=sys.stderr)
        sys.exit(-2)
