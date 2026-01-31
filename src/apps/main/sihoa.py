#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import queue
import logging
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
from logging.handlers import RotatingFileHandler
from logging import Logger
from astral import Observer
from astral.sun import sun
from zoneinfo import ZoneInfo

from src.mqtt.client_manager import ClientManager
from src.data_model.light import Light
from src.data_model.plug import Plug

from typing import List
from typing import Any
from typing import Tuple

def main(manager: ClientManager, inbound_queue: queue.Queue, outbound_queue: queue.Queue, session: Session, logger: Logger) -> None:
    canoves = Observer(latitude=41.694386, longitude=2.352831, elevation=360)
    exterior_porta = Light(ieee_address='d44867fffed60815', friendly_name='exterior_porta', publish_queue=outbound_queue, default_brightness=254, default_color_temp=250)
    exterior_garatge = Light(ieee_address='08fd52fffe0f4080', friendly_name='exterior_garatge', publish_queue=outbound_queue, default_brightness=169, default_color_temp=250)
    exterior_habitacions = Light(ieee_address='180df9fffe88575d', friendly_name='exterior_habitacions', publish_queue=outbound_queue, default_brightness=254, default_color_temp=250)
    pilar_dret = Light(ieee_address='f84477fffef797a4', friendly_name='pilar_dret', publish_queue=outbound_queue, default_brightness=128, default_color_temp=370)
    pilar_esquerre = Light(ieee_address='f84477fffee97eda', friendly_name='pilar_esquerre', publish_queue=outbound_queue, default_brightness=128, default_color_temp=370)
    endoll_aeri_exterior = Plug(ieee_address="a4c1388ae37c8a71", friendly_name="endoll_aeri_exterior", publish_queue=outbound_queue)
    llums: List[Light] = [exterior_porta, pilar_dret, pilar_esquerre, endoll_aeri_exterior, exterior_garatge, exterior_habitacions]
    zigbee_topic = 'zigbee_canoves'
    for llum in llums:
        manager.register(f"{zigbee_topic}/{llum.friendly_name}/availability", llum.on_online)
        manager.register(f"{zigbee_topic}/{llum.friendly_name}", llum.on_get)

    time.sleep(1)

    while True:
        try:
            while True:
                data = outbound_queue.get(timeout=0.1)
                if data is not None:
                    topic: str = data['topic']
                    topic = f"{zigbee_topic}/{topic}"
                    manager.process_outbound_message({'topic': topic, 'payload': data['payload']})
        except queue.Empty:
            pass
        try:
            while True:
                data = inbound_queue.get(timeout=0.1)
                if data is not None:
                    manager.process_inbound_message(data)
        except queue.Empty:
            pass

        today = datetime.datetime.now(timezone.utc)
        cet = ZoneInfo("Europe/Andorra")
        canoves_sun_today = sun(canoves, date=today)
        sunrise = canoves_sun_today['sunrise']
        sunset = canoves_sun_today['sunset']
        llums_sol: List[Light] = [exterior_porta, pilar_dret, pilar_esquerre, endoll_aeri_exterior]
        night = (today >= sunset) or (today < sunrise)
        for llum in llums_sol:
            if night:
                if llum.online:
                    if llum.off:
                        llum.on = True
            else:
                if llum.online:
                    if llum.on:
                        llum.off = True
        llums_hora: List[Light] = [exterior_habitacions, exterior_garatge]
        turn_off_time = datetime.datetime.now(cet)
        turn_off_time = datetime.datetime(year=turn_off_time.year, month=turn_off_time.month, day=turn_off_time.day, hour=4, minute=0, second=0, tzinfo=cet)
        if turn_off_time > sunset:
            # SCENARIO: Off-time is before midnight (e.g., 11 PM)
            # The lights must be AFTER sunset AND BEFORE the off-time.
            should_be_on = (today >= sunset) and (today < turn_off_time)
        else:
            # SCENARIO: Off-time is after midnight (e.g., 4 AM)
            # The lights are on if it's late at night OR very early morning.
            should_be_on = (today >= sunset) or (today < turn_off_time)
        for llum in llums_hora:
            if should_be_on:
                if llum.online:
                    if llum.off:
                        llum.on = True
            else:
                if llum.online:
                    if llum.on:
                        llum.off = True

        time.sleep(0.3)


if __name__ == "__main__":  # pragma: no cover
    # Config the program arguments
    parser = argparse.ArgumentParser(description="SImple HOme Automation application")
    parser.add_argument('-d', '--database', help='SQLite database file', required=False, default=None)
    parser.add_argument("-H", "--host", default="localhost", help="MQTT broker host (default: localhost)")
    parser.add_argument("-p", "--port", type=int, default=1883, help="MQTT broker port (default: 1883)")
    parser.add_argument("-u", "--username", default=None, help="MQTT username (optional)")
    parser.add_argument("-P", "--password", default=None, help="MQTT password (optional)")
    parser.add_argument('-l', '--log-file', help='File to log progress or errors', required=False)
    args = parser.parse_args()

    mqtt_logger = logging.getLogger(__name__)
    if args.log_file is not None:
        handler = RotatingFileHandler(args.log_file, mode='a', maxBytes=5*1024*1024, backupCount=15, encoding='utf-8', delay=False)
        logging.basicConfig(format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s', handlers=[handler], encoding='utf-8', level=logging.DEBUG, datefmt="%Y-%m-%d %H:%M:%S")
    else:
        handler = ch = logging.StreamHandler()
        logging.basicConfig(format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s', handlers=[handler], encoding='utf-8', level=logging.DEBUG, datefmt="%Y-%m-%d %H:%M:%S")

    mqtt_logger.info("Starting SIHOA")
    mqtt_logger.info("Logger running")
    mqtt_logger.info("Connecting to database")
    try:
        engine = create_engine("sqlite:///" + args.database)
        mqtt_database_session = Session(bind=engine)
    except SQLAlchemyError as ex:
        mqtt_logger.fatal(f"Error connecting to database")
        mqtt_logger.exception("Exception")
        sys.exit(-1)
    mqtt_logger.info("Database running")
    mqtt_logger.info("Creating shared message queues")
    mqtt_inbound_queue: queue.Queue = queue.Queue()
    mqtt_outbound_queue: queue.Queue = queue.Queue()
    mqtt_logger.info("Queues running")
    mqtt_logger.info("Connecting to MQTT")
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if (args.username is not None) and (args.password is not None):
        mqtt_client.username_pw_set(username=args.username, password=args.password)
    mqtt_manager = ClientManager(client=mqtt_client, message_queue=mqtt_inbound_queue, logger=mqtt_logger)
    try:
        mqtt_client.on_connect = mqtt_manager.on_connect
        mqtt_client.on_message = mqtt_manager.on_message
        mqtt_client.connect(host=args.host, port=args.port, keepalive=60)
        mqtt_logger.info("MQTT connection with broker running")
        mqtt_logger.info("Starting MQTT loop")
        mqtt_client.loop_start()
        mqtt_logger.info("MQTT loop running")
        timeout = 5
        start_time = time.time()
        while not mqtt_client.is_connected():
            if time.time() - start_time > timeout:
                raise Exception("Failed to connect within timeout")
            time.sleep(0.1)  # Rest the CPU
        mqtt_logger.info("Starting main")
        main(mqtt_manager, mqtt_inbound_queue, mqtt_outbound_queue, mqtt_database_session, mqtt_logger)
    except Exception as xcpt:
        mqtt_logger.fatal(f"MQTT Error")
        mqtt_logger.exception("Exception")
    finally:
        mqtt_logger.info("Stopping MQTT loop")
        mqtt_client.loop_stop()
        mqtt_logger.info("Disconnecting MQTT")
        mqtt_client.disconnect()
        mqtt_logger.info("Finished SIHOA")
        sys.exit(0)