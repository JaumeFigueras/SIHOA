#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import queue
import logging
import json

from typing import NotRequired
from typing import TypedDict
from typing import Unpack
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Any
from paho.mqtt.client import Client
from paho.mqtt.client import ConnectFlags
from paho.mqtt.client import MQTTMessage
from paho.mqtt.reasoncodes import ReasonCode
from paho.mqtt.properties import Properties

class ClientManagerParams(TypedDict):
    client: Client
    message_queue: queue.Queue
    logger: logging.Logger

class ClientManager:
    def __init__(self, **kwargs: Unpack[ClientManagerParams]) -> None:
        self._client: Client = kwargs['client']
        self._message_queue: queue.Queue = kwargs['message_queue']
        self._logger: logging.Logger = kwargs['logger']
        self._registry: Dict[str, Callable] = dict()

    @property
    def client(self) -> Client:
        return self._client

    @client.setter
    def client(self, client: Client) -> None:
        self._client = client

    def register(self, topic: str, callback: Callable) -> None:
        if self._registry.get(topic) is None:
            self._registry[topic] = callback
            result, _ = self._client.subscribe(topic)
            if result != 0:
                raise Exception(f"Subscription to {topic} caused an error")
            self._logger.info(f"Subscribed to {topic} successfully")
        else:
            raise Exception(f"Client {topic} already registered")

    def unregister(self, topic: str) -> Callable:
        if self._registry.get(topic) is not None:
            result, _ = self._client.unsubscribe(topic)
            if result != 0:
                raise Exception(f"Unsubscription to {topic} caused an error")
            self._logger.info(f"Unsubscribed from {topic} successfully")
            return self._registry.pop(topic)
        else:
            raise Exception(f"Client {topic} not registered")

    def process_inbound_message(self, data: Dict[str, Any]) -> None:
        topic = data['topic']
        message = data['payload']
        callback = self._registry.get(topic)
        callback(message)

    def process_outbound_message(self, data: Dict[str, Any]) -> None:
        topic = data['topic']
        payload = data['payload']
        self._logger.info(f"Message to {topic} with payload {payload} sent")
        self._client.publish(topic, json.dumps(payload))

    def on_connect(self, client: Client, userdata: Any, flags: ConnectFlags, reason_code: ReasonCode, properties: Properties) -> None:
        if reason_code == 0:
            self._logger.info("Connected successfully")
            # In case of disconnection and automatic re-connect
            for topic in self._registry.keys():
                client.subscribe(topic)
        else:
            self._logger.fatal(f"Connection failed with code: {reason_code}")
            raise Exception(f"Connection failed with code: {reason_code}")

    def on_message(self, client: Client, userdata: Any, msg: MQTTMessage) -> None:
        if self._registry.get(msg.topic) is not None:
            self._logger.info(f"Message from {msg.topic} received successfully with payload: {msg.payload}")
            data = json.loads(msg.payload.decode('utf-8'))
            self._message_queue.put({"topic": msg.topic, "payload": data})
        else:
            self._logger.fatal(f"Message from {msg.topic} received but not registered")
            raise Exception(f"Message topic {msg.topic} not registered")

