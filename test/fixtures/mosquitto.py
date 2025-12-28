#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Session-scoped fixture to ensure a local Mosquitto broker is available.

Behavior:
- If something is already listening on localhost:1883, assumes a broker is running and uses it.
- Otherwise, attempts to start Mosquitto on localhost:1883 using a temporary config.
- Skips the test session if 'mosquitto' executable is not found.
- Cleanly terminates the broker when the session ends.

Requires Mosquitto installed on the system (command: 'mosquitto').
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import tempfile
import time
from typing import Iterator, Tuple

import pytest


def _wait_for_port(host: str, port: int, timeout: float = 5.0) -> bool:
    """Wait until a TCP port is accepting connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


@pytest.fixture(scope="session")
def local_mosquitto() -> Iterator[Tuple[str, int]]:
    """
    Ensure a Mosquitto broker is available on localhost:1883 for the test session.

    Returns
    -------
    (host, port) : tuple[str, int]
        The host and port where the broker is listening (typically "localhost", 1883).
    """
    host: str = "localhost"
    port: int = 1883

    # If a broker is already running, use it.
    if _wait_for_port(host, port, timeout=0.5):
        yield host, port
        return

    # Otherwise, try to start Mosquitto locally.
    # if shutil.which("mosquitto") is None:
    #     pytest.skip(
    #         "Mosquitto executable not found. Install Mosquitto or run pytest with an existing broker "
    #         "via --mqtt-host/--mqtt-port and ensure it is reachable."
    #     )

    with tempfile.TemporaryDirectory(prefix="mosq_") as tmpdir:
        conf_path = os.path.join(tmpdir, "mosquitto.conf")
        # Minimal config: listen on 1883, allow anonymous, no persistence
        with open(conf_path, "w", encoding="utf-8") as f:
            f.write(
                f"listener {port}\n"
                "allow_anonymous true\n"
                "persistence false\n"
                "log_type error\n"
            )

        proc = subprocess.Popen(
            ["mosquitto", "-c", conf_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        try:
            if not _wait_for_port(host, port, timeout=5.0):
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except Exception:
                    pass
                pytest.skip("Failed to start local Mosquitto broker on localhost:1883")
            yield host, port
        finally:
            # Attempt graceful shutdown
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except Exception:
                proc.kill()