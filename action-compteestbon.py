#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hermes_python.hermes import Hermes
from hermes_python.ffi.utils import MqttOptions

state = {'nbNumbers': 3}


def humaniser(nombre):
    nombre = round(nombre, 4)
    if str(nombre)[-2:] == ".0":
        nombre = int(nombre)
    return nombre


def start_lecompteestbon(hermes, intent_message):
    phrase = "C'est parti pour le compte est bon"
    hermes.publish_end_session(intent_message.session_id, phrase)


if __name__ == "__main__":
    mqtt_opts = MqttOptions()
    with Hermes(mqtt_options=mqtt_opts) as h:
        h.subscribe_intent(
            "abienvenu:startLeCompteEstBon",
            start_lecompteestbon
        ).start()
