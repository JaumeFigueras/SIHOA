#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the Device SQLAlchemy model.

These tests validate:
- Minimal creation with required fields and default values.
- Creation with optional fields and type persistence.
- String representation (__repr__) includes key identifiers.
- Check constraint on network_address range (0..65535).
- Uniqueness constraints for both friendly_name and primary key (ieee_address).
- Manual retirement timestamp handling (retired_at).
- Constructor behavior ignoring unknown kwargs.

The tests rely on the pytest fixtures defined in:
- test/conftest.py
- test/fixtures/database.py

All tests use only libraries listed in requirements.txt.
"""

from __future__ import annotations

import pytest

from datetime import date
from datetime import datetime
from datetime import timezone
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.data_model.device import Device

from typing import Optional

def test_device_creation_minimal(db_session: Session) -> None:
    """Create a Device with only required fields and verify defaults are set.

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session fixture bound to the test database.

    Returns
    -------
    None
    """
    d: Device = Device(ieee_address="0x00124B0012345678", friendly_name="Kitchen Light")
    db_session.add(d)
    db_session.commit()
    db_session.refresh(d)

    got: Optional[Device] = db_session.get(Device, "0x00124B0012345678")
    assert got is not None
    assert got.ieee_address == "0x00124B0012345678"
    assert got.friendly_name == "Kitchen Light"
    assert got.network_address is None
    assert got.firmware_build_date is None
    assert got.firmware_version is None
    assert got.device_type is None
    assert got.zigbee_model is None
    assert got.zigbee_manufacturer is None
    assert got.created_at is not None
    assert got.retired_at is None


def test_device_creation_with_optional_fields(db_session: Session) -> None:
    """Create a Device with optional fields and ensure values persist as expected.

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session fixture bound to the test database.

    Returns
    -------
    None
    """
    d: Device = Device(
        ieee_address="0x00124B00ABCDEF01",
        friendly_name="Hall Switch",
        network_address=0x1234,
        firmware_build_date=date(2024, 12, 25),
        firmware_version="1.2.3",
        device_type="switch",
        zigbee_model="ZB-SW-100",
        zigbee_manufacturer="Acme",
    )
    db_session.add(d)
    db_session.commit()

    got: Optional[Device] = db_session.get(Device, "0x00124B00ABCDEF01")
    assert got is not None
    assert got.network_address == 0x1234
    assert got.firmware_build_date == date(2024, 12, 25)
    assert got.firmware_version == "1.2.3"
    assert got.device_type == "switch"
    assert got.zigbee_model == "ZB-SW-100"
    assert got.zigbee_manufacturer == "Acme"


def test_repr_contains_key_fields(db_session: Session) -> None:
    """Verify the __repr__ string includes ieee_address and friendly_name.

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session fixture bound to the test database.

    Returns
    -------
    None
    """
    d: Device = Device(ieee_address="0x00124B0099998888", friendly_name="Desk Lamp")
    s: str = repr(d)
    assert "0x00124B0099998888" in s
    assert "Desk Lamp" in s


def test_network_address_range_valid(db_session: Session) -> None:
    """Accept network_address values at the bounds (0 and 65535).

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session fixture bound to the test database.

    Returns
    -------
    None
    """
    d1: Device = Device(ieee_address="0x00124B0000000001", friendly_name="Dev1", network_address=0)
    d2: Device = Device(ieee_address="0x00124B0000000002", friendly_name="Dev2", network_address=65535)
    db_session.add_all([d1, d2])
    db_session.commit()

    got1: Optional[Device] = db_session.get(Device, "0x00124B0000000001")
    got2: Optional[Device] = db_session.get(Device, "0x00124B0000000002")
    assert got1 is not None and got1.network_address == 0
    assert got2 is not None and got2.network_address == 65535


def test_network_address_range_invalid_high(db_session: Session) -> None:
    """Reject network_address values above 65535 (violates CheckConstraint).

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session fixture bound to the test database.

    Returns
    -------
    None
    """
    d: Device = Device(ieee_address="0x00124B00000000AA", friendly_name="TooHigh", network_address=65536)
    db_session.add(d)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_network_address_range_invalid_negative(db_session: Session) -> None:
    """Reject negative network_address values (violates CheckConstraint).

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session fixture bound to the test database.

    Returns
    -------
    None
    """
    d: Device = Device(ieee_address="0x00124B00000000BB", friendly_name="Negative", network_address=-1)
    db_session.add(d)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_unique_friendly_name(db_session: Session) -> None:
    """Enforce unique constraint on friendly_name across devices.

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session fixture bound to the test database.

    Returns
    -------
    None
    """
    d1: Device = Device(ieee_address="0x00124B00000000C1", friendly_name="UniqueName")
    d2: Device = Device(ieee_address="0x00124B00000000C2", friendly_name="UniqueName")  # duplicate name
    db_session.add(d1)
    db_session.commit()

    db_session.add(d2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_primary_key_uniqueness_ieee_address(db_session: Session) -> None:
    """Enforce primary key uniqueness for ieee_address.

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session fixture bound to the test database.

    Returns
    -------
    None
    """
    d1: Device = Device(ieee_address="0x00124B00DUPLICATE", friendly_name="Name1")
    d2: Device = Device(ieee_address="0x00124B00DUPLICATE", friendly_name="Name2")  # duplicate PK
    db_session.add(d1)
    db_session.commit()

    db_session.add(d2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_retired_at_setting(db_session: Session) -> None:
    """Manually set retired_at and verify it persists.

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session fixture bound to the test database.

    Returns
    -------
    None
    """
    d: Device = Device(ieee_address="0x00124B00RETIRE001", friendly_name="Garden Light")
    db_session.add(d)
    db_session.commit()

    d.retired_at = datetime.now(timezone.utc)
    db_session.commit()

    got: Optional[Device] = db_session.get(Device, "0x00124B00RETIRE001")
    assert got is not None and got.retired_at is not None


def test_constructor_ignores_unknown_keys(db_session: Session) -> None:
    """Constructor must ignore unknown kwargs and not create new attributes.

    Parameters
    ----------
    db_session : Session
        SQLAlchemy session fixture bound to the test database.

    Returns
    -------
    None
    """
    d: Device = Device(ieee_address="0x00124B00UNKNOWN01", friendly_name="Unknown Test", unknown_field="ignored")
    assert not hasattr(d, "unknown_field")
