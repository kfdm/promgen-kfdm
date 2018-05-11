# https://github.com/todbot/blink1/blob/master/docs/app-url-api-examples.md
import fnmatch
import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

import paho.mqtt.client as mqtt
import requests

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('blink(1)')


class EventDispatch(object):
    def __init__(self):
        self.events = []

    def register(self, glob):
        def wrapper(func):
            logger.info('register: %s %s', glob, func)
            self.events.append((glob, func))
        return wrapper

    def process(self, client, userdata, msg):
        data = json.loads(msg.payload.decode('utf8'))
        logger.debug('Process: %s %s', msg.topic, data)
        for glob, func in self.events:
            if fnmatch.fnmatch(msg.topic, glob):
                try:
                    func(msg.topic, data)
                except:
                    pass

dispatch = EventDispatch()


@dispatch.register('pomodoro/*/nag')
def pomodoro(topic, data):
    print(topic, data)
    requests.get('http://localhost:8934/blink1/pattern/play', params={
        'pname': 'pomodoro-red'
    }).raise_for_status()


@dispatch.register('promgen*')
def alert(topic, data):
    print(topic, data)
    requests.get('http://localhost:8934/blink1/pattern/play', params={
        'pname': 'lightingstorm'
    }).raise_for_status()


@dispatch.register('owntracks/*')
def healthcheck(topic, data):
    logger.info('Sending health check')
    requests.post('https://hchk.io/d2e37e5d-18c7-4109-bfff-d57756b20ef2')


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    logger.info("Connected with result code %s", rc)

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("#")


class Command(BaseCommand):
    def handle(self, **options):
        s = settings.PROMGEN['promgenkfdm.notification.mqtt']

        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = dispatch.process
        client.username_pw_set(s['user'], password=s['pass'])

        client.connect(s['host'], 1883, 60)

        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.
        try:
            client.loop_forever()
        except KeyboardInterrupt:
            pass
