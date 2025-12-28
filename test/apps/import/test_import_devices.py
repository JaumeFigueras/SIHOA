#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import json

import src.apps.imports.import_devices as mod

from datetime import date
from datetime import datetime

from typing import Any
from typing import Tuple
from typing import List
from typing import Dict
from typing import Optional


@pytest.mark.parametrize("mqtt_payload", ["base/bridge/devices"], indirect=True)
def test_payload(mqtt_payload):
    assert mqtt_payload[0]["friendly_name"] == "Coordinator"

@pytest.mark.parametrize("mqtt_payload", ["base/bridge/devices"], indirect=True)
def test_read_zigbee2mqtt_devices_returns_list(
    mqtt_payload: List[Dict[str, Any]],
    local_mosquitto: Tuple[str, int],
    capmqtt,    # provided by pytest-mqtt
) -> None:
    """Ensure the function returns the retained device list as a Python list.

    Parameters
    ----------
    mqtt_payload : list[dict[str, Any]]
        Sample JSON payload loaded by the mqtt fixture for the topic 'base/bridge/devices'.
    local_mosquitto : Any
        Session-scoped broker fixture from pytest-mqtt. Ensures a Mosquitto broker is available.
    capmqtt : Any
        MQTT capture/publish fixture from pytest-mqtt, used to publish retained messages.

    Returns
    -------
    None
    """
    topic: str = "base/bridge/devices"
    # Publish retained message so subscribers receive it immediately.
    capmqtt.publish(topic=topic, payload=json.dumps(mqtt_payload), retain=True)

    devices: list[dict[str, Any]] = mod.read_zigbee2mqtt_devices(
        host="localhost",   # pytest-mqtt defaults
        port=1883,          # pytest-mqtt defaults
        topic=topic,
        timeout_s=1.0,
        username=None,
        password=None,
    )

    assert isinstance(devices, list)
    assert devices == mqtt_payload


@pytest.mark.parametrize("mqtt_payload", ["base/bridge/devices"], indirect=True)
def test_read_zigbee2mqtt_devices_wrong_topic_times_out(
    mqtt_payload: List[Dict[str, Any]],
    local_mosquitto: Tuple[str, int],
    capmqtt,
) -> None:
    """If a different topic is requested, the function should ignore retained messages and return an empty list.

    Parameters
    ----------
    mqtt_payload : list[dict[str, Any]]
        Sample JSON payload loaded for the topic 'base/bridge/devices'.
    local_mosquitto : tuple[str, int]
        Host and port tuple for the locally managed Mosquitto broker.
    capmqtt : Any
        MQTT capture/publish fixture from pytest-mqtt.

    Returns
    -------
    None
    """
    host, port = local_mosquitto

    # Publish retained payload on the base topic
    capmqtt.publish(topic="base/bridge/devices", payload=json.dumps(mqtt_payload), retain=True)

    # Call with a different topic; should not receive the retained payload
    devices: List[Dict[str, Any]] = mod.read_zigbee2mqtt_devices(
        host=host,
        port=port,
        topic="other/topic",
        timeout_s=0.2,
    )

    assert devices == []


def test_read_zigbee2mqtt_devices_invalid_payload_returns_empty(
    local_mosquitto: Tuple[str, int],
    capmqtt,
) -> None:
    """If the retained payload is valid JSON but not a list, the function should return an empty list.

    Parameters
    ----------
    local_mosquitto : tuple[str, int]
        Host and port tuple for the locally managed Mosquitto broker.
    capmqtt : Any
        MQTT capture/publish fixture from pytest-mqtt.

    Returns
    -------
    None
    """
    host, port = local_mosquitto
    topic: str = "base/bridge/devices"
    invalid_structure: str = '{"not": "a list"}'  # valid JSON, wrong type (dict instead of list)

    capmqtt.publish(topic=topic, payload=invalid_structure, retain=True)

    devices: List[Dict[str, Any]] = mod.read_zigbee2mqtt_devices(
        host=host,
        port=port,
        topic=topic,
        timeout_s=0.2,
    )

    assert devices == []


def test_read_zigbee2mqtt_devices_empty_list_payload_returns_empty(
    local_mosquitto: Tuple[str, int],
    capmqtt,
) -> None:
    """If the retained payload is an empty list, the function should return an empty list.

    Parameters
    ----------
    local_mosquitto : tuple[str, int]
        Host and port tuple for the locally managed Mosquitto broker.
    capmqtt : Any
        MQTT capture/publish fixture from pytest-mqtt.

    Returns
    -------
    None
    """
    host, port = local_mosquitto
    topic: str = "base/bridge/devices"

    capmqtt.publish(topic=topic, payload="[]", retain=True)

    devices: List[Dict[str, Any]] = mod.read_zigbee2mqtt_devices(
        host=host,
        port=port,
        topic=topic,
        timeout_s=0.2,
    )

    assert devices == []


def test_read_zigbee2mqtt_devices_no_payload_returns_empty(
    local_mosquitto: Tuple[str, int],
) -> None:
    """If there is no retained message for the topic, the function should return an empty list after timeout.

    Parameters
    ----------
    local_mosquitto : tuple[str, int]
        Host and port tuple for the locally managed Mosquitto broker.

    Returns
    -------
    None
    """
    host, port = local_mosquitto
    topic: str = "base/bridge/devices"

    devices: List[Dict[str, Any]] = mod.read_zigbee2mqtt_devices(
        host=host,
        port=port,
        topic=topic,
        timeout_s=0.2,  # short timeout to keep test fast
    )

    assert devices == []


def test_read_zigbee2mqtt_devices_malformed_json_returns_empty(local_mosquitto: Tuple[str, int], capmqtt) -> None:
    """If the retained payload is malformed JSON, json.JSONDecodeError should be raised by the on_message handler.

    Parameters
    ----------
    local_mosquitto : tuple[str, int]
        Host and port tuple for the locally managed Mosquitto broker.
    capmqtt : Any
        MQTT capture/publish fixture from pytest-mqtt.

    Returns
    -------
    None
    """
    host, port = local_mosquitto
    topic: str = "base/bridge/devices"
    malformed: str = '{"missing": "brace"'  # invalid JSON

    capmqtt.publish(topic=topic, payload=malformed, retain=True)

    devices: List[Dict[str, Any]] = mod.read_zigbee2mqtt_devices(host=host, port=port, topic=topic, timeout_s=0.5)
    assert devices == []


def test_read_zigbee2mqtt_devices_invalid_utf8_returns_empty(
    local_mosquitto: Tuple[str, int],
    capmqtt,
) -> None:
    """If the retained payload is not valid UTF-8, the function should return an empty list.

    Parameters
    ----------
    local_mosquitto : tuple[str, int]
        Host and port tuple for the locally managed Mosquitto broker.
    capmqtt : Any
        MQTT capture/publish fixture from pytest-mqtt.

    Returns
    -------
    None
    """
    host, port = local_mosquitto
    topic: str = "base/bridge/devices"
    invalid_bytes: bytes = b"\xff\xfe\xfa"  # invalid UTF-8 sequence

    capmqtt.publish(topic=topic, payload=invalid_bytes, retain=True)

    devices: List[Dict[str, Any]] = mod.read_zigbee2mqtt_devices(
        host=host,
        port=port,
        topic=topic,
        timeout_s=0.5,
    )

    assert devices == []


def test_parse_date_maybe_none_returns_none() -> None:
    """None input should return None.

    Returns
    -------
    None
    """
    assert mod._parse_date_maybe(None) is None


def test_parse_date_maybe_date_passthrough() -> None:
    """A date instance should be returned unchanged.

    Returns
    -------
    None
    """
    d: date = date(2024, 12, 25)
    got: Optional[date] = mod._parse_date_maybe(d)
    assert got == d


def test_parse_date_maybe_datetime_returns_date() -> None:
    """A datetime instance should return its date component.

    Returns
    -------
    None
    """
    dt: datetime = datetime(2024, 12, 25, 10, 30, 45, tzinfo=timezone.utc)
    got: Optional[date] = mod._parse_date_maybe(dt)
    assert got == date(2024, 12, 25)


def test_parse_date_maybe_iso_date_string() -> None:
    """ISO date string 'YYYY-MM-DD' should parse to a date.

    Returns
    -------
    None
    """
    s: str = "2024-12-25"
    got: Optional[date] = mod._parse_date_maybe(s)
    assert got == date(2024, 12, 25)


def test_parse_date_maybe_iso_datetime_string_z() -> None:
    """ISO datetime string with 'Z' should parse and return the date component.

    Returns
    -------
    None
    """
    s: str = "2024-12-25T10:23:45Z"
    got: Optional[date] = mod._parse_date_maybe(s)
    assert got == date(2024, 12, 25)


def test_parse_date_maybe_iso_datetime_fractional_seconds() -> None:
    """ISO datetime string with fractional seconds should parse and return the date component.

    Returns
    -------
    None
    """
    s: str = "2024-12-25T10:23:45.123Z"
    got: Optional[date] = mod._parse_date_maybe(s)
    assert got == date(2024, 12, 25)


def test_parse_date_maybe_rfc2822_like_string() -> None:
    """RFC2822-like date strings (supported by dateutil) should parse to date.

    Returns
    -------
    None
    """
    s: str = "Sat, 28 Dec 2024 10:00:00 GMT"
    got: Optional[date] = mod._parse_date_maybe(s)
    assert got == date(2024, 12, 28)


def test_parse_date_maybe_invalid_string_returns_none() -> None:
    """Unparseable string should return None.

    Returns
    -------
    None
    """
    s: str = "not-a-date"
    got: Optional[date] = mod._parse_date_maybe(s)
    assert got is None


def test_parse_date_maybe_non_string_returns_none() -> None:
    """Non-string, non-date/datetime inputs should return None.

    Returns
    -------
    None
    """
    val_int: int = 123456
    val_float: float = 123.456
    class Dummy: ...
    val_obj: Any = Dummy()

    assert mod._parse_date_maybe(val_int) is None
    assert mod._parse_date_maybe(val_float) is None
    assert mod._parse_date_maybe(val_obj) is None


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for store_devices_to_db in src.apps.import.import_devices.

These tests validate:
- Creation of new devices and correct processed/retired counts.
- Update of existing devices and clearing of retired_at when device is active.
- Retirement of devices missing from the retained list (only those not already retired).
- Skipping invalid entries missing essential identifiers.
- Preserving previous network_address on conversion failure.
- Parsing of firmware build date from multiple possible fields.

Only libraries listed in requirements.txt are used.
"""




from sqlalchemy.orm import Session
from src.data_model.device import Device


def test_store_devices_creates_new_devices(db_session: Session) -> None:
    """Create new devices from retained descriptors.

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session fixture bound to the test database.

    Returns
    -------
    None
    """
    devices: List[Dict[str, Any]] = [
        {
            "ieee_address": "0x00124B00AAAABBBB",
            "friendly_name": "Living Room Lamp",
            "network_address": 0x1001,
            "software_version": "1.0.0",
            "manufacturer": "VendorA",
            "model": "ModelA",
            "software_build_id": "2024-12-25",
        },
        {
            "ieeeAddress": "0x00124B00CCCCDDDD",  # camelCase variant
            "friendlyName": "Hallway Sensor",     # camelCase variant
            "networkAddress": 0x2002,             # camelCase variant
            "firmware_version": "2.3.4",
            "zigbee_manufacturer": "VendorB",
            "zigbee_model": "ModelB",
            "date_code": "2024-12-26",
        },
    ]

    processed, retired = mod.store_devices_to_db(db_session, devices)
    assert processed == 2
    assert retired == 0

    d1: Optional[Device] = db_session.get(Device, "0x00124B00AAAABBBB")
    d2: Optional[Device] = db_session.get(Device, "0x00124B00CCCCDDDD")
    assert d1 is not None and d2 is not None

    assert d1.friendly_name == "Living Room Lamp"
    assert d1.network_address == 0x1001
    assert d1.firmware_version == "1.0.0"
    assert d1.zigbee_manufacturer == "VendorA"
    assert d1.zigbee_model == "ModelA"
    assert d1.firmware_build_date == date(2024, 12, 25)
    assert d1.retired_at is None

    assert d2.friendly_name == "Hallway Sensor"
    assert d2.network_address == 0x2002
    assert d2.firmware_version == "2.3.4"
    assert d2.zigbee_manufacturer == "VendorB"
    assert d2.zigbee_model == "ModelB"
    assert d2.firmware_build_date == date(2024, 12, 26)
    assert d2.retired_at is None


def test_store_devices_updates_existing_and_clears_retired_at(db_session: Session) -> None:
    """Update existing device fields and clear retired_at for active devices.

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session fixture bound to the test database.

    Returns
    -------
    None
    """
    # Pre-create existing device with retired_at set
    pre: Device = Device(
        ieee_address="0x00124B00EEEEFFFF",
        friendly_name="Old Name",
        network_address=5,
    )
    db_session.add(pre)
    db_session.commit()

    # Mark retired (simulate previously retired device)
    pre.retired_at = datetime.now(timezone.utc)
    db_session.commit()

    devices: List[Dict[str, Any]] = [
        {
            "ieee_address": "0x00124B00EEEEFFFF",
            "friendly_name": "New Name",
            "network_address": "10",  # string convertible to int
            "software_version": "9.9.9",
            "manufacturer": "VendorX",
            "model": "ModelX",
            "firmware_build_date": "2024-12-20",
        }
    ]

    processed, retired = mod.store_devices_to_db(db_session, devices)
    assert processed == 1
    assert retired == 0

    got: Optional[Device] = db_session.get(Device, "0x00124B00EEEEFFFF")
    assert got is not None
    assert got.friendly_name == "New Name"
    assert got.network_address == 10
    assert got.firmware_version == "9.9.9"
    assert got.zigbee_manufacturer == "VendorX"
    assert got.zigbee_model == "ModelX"
    assert got.firmware_build_date == date(2024, 12, 20)
    # Active device should be un-retired
    assert got.retired_at is None


def test_store_devices_retire_missing_nonretired(db_session: Session) -> None:
    """Retire devices missing from retained list (only those not already retired).

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session fixture bound to the test database.

    Returns
    -------
    None
    """
    d1: Device = Device(ieee_address="0x00124B00FFFF0001", friendly_name="KeepMe", network_address=0x3003)
    d2: Device = Device(ieee_address="0x00124B00FFFF0002", friendly_name="RetireMe", network_address=0x3004)
    db_session.add_all([d1, d2])
    db_session.commit()

    devices: List[Dict[str, Any]] = [
        {"ieee_address": "0x00124B00FFFF0001", "friendly_name": "KeepMe"}  # only d1 is active
    ]

    processed, retired = mod.store_devices_to_db(db_session, devices)
    assert processed == 1
    assert retired == 1

    kept: Optional[Device] = db_session.get(Device, "0x00124B00FFFF0001")
    gone: Optional[Device] = db_session.get(Device, "0x00124B00FFFF0002")

    assert kept is not None and kept.retired_at is None
    assert gone is not None and gone.retired_at is not None


def test_store_devices_does_not_retire_already_retired(db_session: Session) -> None:
    """Ensure already retired devices are not counted or modified during retirement pass.

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session fixture bound to the test database.

    Returns
    -------
    None
    """
    retired_dev: Device = Device(ieee_address="0x00124B00RET0001", friendly_name="AlreadyRetired")
    db_session.add(retired_dev)
    db_session.commit()

    retired_dev.retired_at = datetime(2024, 12, 1)
    db_session.commit()

    # No active devices provided
    devices: List[Dict[str, Any]] = []

    processed, retired = mod.store_devices_to_db(db_session, devices)
    assert processed == 0
    # Because select filters only non-retired devices, this remains 0
    assert retired == 0

    got: Optional[Device] = db_session.get(Device, "0x00124B00RET0001")
    assert got is not None
    assert got.retired_at == datetime(2024, 12, 1)


def test_store_devices_skips_invalid_entries_missing_identifiers(db_session: Session) -> None:
    """Skip entries missing ieee_address or friendly_name; do not create/update them.

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session fixture bound to the test database.

    Returns
    -------
    None
    """
    devices: List[Dict[str, Any]] = [
        {"friendly_name": "NoIEEE"},  # missing ieee_address
        {"ieee_address": "0x00124B00BAD0001"},  # missing friendly_name
        {"ieee_address": "0x00124B00GOOD0001", "friendly_name": "GoodOne"},
    ]

    processed, retired = mod.store_devices_to_db(db_session, devices)
    assert processed == 1
    assert retired == 0

    assert db_session.get(Device, "0x00124B00BAD0001") is None
    assert db_session.get(Device, "0x00124B00GOOD0001") is not None


def test_store_devices_preserves_network_address_on_conversion_failure(db_session: Session) -> None:
    """If network_address cannot be converted to int, keep previous value.

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session fixture bound to the test database.

    Returns
    -------
    None
    """
    existing: Device = Device(
        ieee_address="0x00124B00NETADDR01",
        friendly_name="NetAddr",
        network_address=33,
    )
    db_session.add(existing)
    db_session.commit()

    devices: List[Dict[str, Any]] = [
        {"ieee_address": "0x00124B00NETADDR01", "friendly_name": "NetAddr", "network_address": "not-an-int"}
    ]

    processed, retired = mod.store_devices_to_db(db_session, devices)
    assert processed == 1
    assert retired == 0

    got: Optional[Device] = db_session.get(Device, "0x00124B00NETADDR01")
    assert got is not None
    assert got.network_address == 33  # unchanged


def test_store_devices_parses_build_date_from_various_fields(db_session: Session) -> None:
    """Firmware build date is parsed from software_build_id, firmware_build_date, or date_code.

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session fixture bound to the test database.

    Returns
    -------
    None
    """
    devices: List[Dict[str, Any]] = [
        {
            "ieee_address": "0x00124B00DATE0001",
            "friendly_name": "BuildID",
            "software_build_id": "2024-12-21",
        },
        {
            "ieee_address": "0x00124B00DATE0002",
            "friendly_name": "FirmwareBuildDate",
            "firmware_build_date": "2024-12-22",
        },
        {
            "ieee_address": "0x00124B00DATE0003",
            "friendly_name": "DateCode",
            "date_code": "2024-12-23",
        },
    ]

    processed, retired = mod.store_devices_to_db(db_session, devices)
    assert processed == 3
    assert retired == 0

    d1: Optional[Device] = db_session.get(Device, "0x00124B00DATE0001")
    d2: Optional[Device] = db_session.get(Device, "0x00124B00DATE0002")
    d3: Optional[Device] = db_session.get(Device, "0x00124B00DATE0003")

    assert d1 is not None and d1.firmware_build_date == date(2024, 12, 21)
    assert d2 is not None and d2.firmware_build_date == date(2024, 12, 22)
    assert d3 is not None and d3.firmware_build_date == date(2024, 12, 23)