# https://github.com/todbot/blink1/blob/master/docs/app-url-api-examples.md
import json

from django.conf import settings
from django.core.management.base import BaseCommand

import paho.mqtt.client as mqtt
import requests


def pomodoro(topic, data):
    print(topic, data)
    if data['diff'] < 0:
        requests.get('http://localhost:8934/blink1/fadeToRGB', params={
            'rgb': 'green'
        })
    elif data['diff'] < 300:
        requests.get('http://localhost:8934/blink1/fadeToRGB', params={
            'rgb': 'blue'
        })
    else:
        requests.get('http://localhost:8934/blink1/pattern/play', params={
            'pname': 'pomodoro-red'
        }).raise_for_status()

def alert(topic, data):
    print(topic, data)
    requests.get('http://localhost:8934/blink1/pattern/play', params={
        'pname': 'lightingstorm'
    }).raise_for_status()


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("pomodoro/kfdm")
    client.subscribe("promgen/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode('utf8'))
    if msg.topic.startswith('pomodoro'):
        pomodoro(msg.topic, data)
    if msg.topic.startswith('promgen'):
        alert(msg.topic, data)





class Command(BaseCommand):
    def handle(self, **options):
        s = settings.PROMGEN['promgenkfdm.notification.mqtt']

        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        client.username_pw_set(s['user'], password=s['pass'])

        client.connect(s['host'], 1883, 60)

        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.
        client.loop_forever()
