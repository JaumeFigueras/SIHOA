#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Device model and constructor parameters for SIHOA.

This module defines:
- Device: SQLAlchemy declarative model representing a generic Zigbee device.
- DeviceParams: TypedDict describing the keyword arguments accepted by the
  Device constructor.

Notes
-----
- The Device class captures stable, persistent attributes (identities and static
  metadata). Volatile runtime state and messaging details are intentionally not
  persisted here and will be handled by other components.
- The Zigbee IEEE address is used as the primary key. It is a globally unique,
  permanent 64-bit identifier assigned at manufacturing time.
- Two lifecycle timestamps are included:
  - created_at: when the device record was created in the database.
  - retired_at: when the device was marked as no longer available (optional).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import NotRequired, TypedDict, Unpack

from sqlalchemy import CheckConstraint, Date, DateTime, String, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class DeviceParams(TypedDict):
    """Keyword parameters accepted by the Device constructor.

    Parameters
    ----------
    ieee_address : str
        Unique, permanent 64-bit Zigbee IEEE (extended) address (e.g., '0x00124B0012345678').
        This is the primary key of the model.
    friendly_name : str
        Human-friendly device name. Must be unique.
    network_address : NotRequired[int]
        16-bit Zigbee network (short) address. Optional and may change over time.
    firmware_build_date : NotRequired[date]
        Firmware build or release date.
    firmware_version : NotRequired[str]
        Firmware version string.
    device_type : NotRequired[str]
        Logical device type (e.g., 'bulb', 'switch', 'socket', 'button').
    zigbee_model : NotRequired[str]
        Reported Zigbee model identifier (e.g., from device descriptors).
    zigbee_manufacturer : NotRequired[str]
        Reported Zigbee manufacturer name.
    retired_at : NotRequired[datetime]
        Timestamp when the device was marked as no longer available.
        Leave unset for active devices.
    """
    ieee_address: str
    friendly_name: str
    network_address: NotRequired[int]
    firmware_build_date: NotRequired[date]
    firmware_version: NotRequired[str]
    device_type: NotRequired[str]
    zigbee_model: NotRequired[str]
    zigbee_manufacturer: NotRequired[str]
    retired_at: NotRequired[datetime]


class Device(Base):
    """Generic device model for Zigbee devices handled via MQTT.

    Attributes
    ----------
    ieee_address : str
        Primary key. Unique 64-bit Zigbee IEEE (extended) address as a string.
    friendly_name : str
        Human-friendly unique name for the device.
    network_address : int or None
        16-bit Zigbee network (short) address. May change due to rejoin/rebind.
    firmware_build_date : date or None
        Firmware build or release date.
    firmware_version : str or None
        Firmware version string.
    device_type : str or None
        Logical device type (e.g., 'bulb', 'switch', 'socket', 'button').
    zigbee_model : str or None
        Zigbee-reported model identifier.
    zigbee_manufacturer : str or None
        Zigbee-reported manufacturer name.
    created_at : datetime
        Timestamp when the device row was created in the database (UTC recommended).
    retired_at : datetime or None
        Timestamp when the device was marked as no longer available.
    """

    __tablename__ = "device"
    __table_args__ = (
        # Ensure the 16-bit network address, if set, remains within valid range.
        CheckConstraint(
            "(network_address IS NULL) OR (network_address >= 0 AND network_address <= 65535)",
            name="ck_device_network_address_range",
        ),
    )

    # Primary identity: Zigbee IEEE (extended) address as string.
    # Stored as string to preserve canonical hex representation (e.g., '0x00124B0012345678').
    ieee_address: Mapped[str] = mapped_column(String(24), primary_key=True)

    # Friendly unique name for easier user reference.
    friendly_name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    # 16-bit short network address (dynamic).
    network_address: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Firmware metadata.
    firmware_build_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(60), nullable=True)

    # Device identity and classification as reported by Zigbee.
    device_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    zigbee_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    zigbee_manufacturer: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Lifecycle timestamps.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __init__(self, **kwargs: Unpack[DeviceParams]) -> None:
        """Initialize a Device instance from keyword parameters.

        Parameters
        ----------
        **kwargs : Unpack[DeviceParams]
            Keyword arguments matching DeviceParams. Unknown keys are ignored.

        Notes
        -----
        - `created_at` is set automatically by the database default and should
          not be provided during construction in typical usage.
        - Unknown keys are safely ignored to prevent accidental attribute creation.
        """
        super().__init__()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self) -> str:
        """Return a concise representation of the device.

        Returns
        -------
        str
            String representation including ieee_address and friendly_name.
        """
        return (
            f"Device(ieee_address={getattr(self, 'ieee_address', None)!r}, "
            f"friendly_name={getattr(self, 'friendly_name', None)!r})"
        )
