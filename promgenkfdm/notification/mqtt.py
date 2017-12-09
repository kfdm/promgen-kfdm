import json

from django import forms

import paho.mqtt.client as mqtt
from promgen.notification import NotificationBase


class FormMQTT(forms.Form):
    value = forms.CharField(
        required=True,
        label='MQTT Topic'
    )


class NotificationMQTT(NotificationBase):
    form = FormMQTT

    def _send(self, topic, data):
        client = mqtt.Client()
        client.username_pw_set(self.config('user'), password= self.config('pass'))
        client.connect(self.config('host'), 1883, 60)
        for alert in data['alerts']:
            if 'labels' in alert:
                client.publish(topic, json.dumps(alert['labels']).encode('utf8'))
        return True
