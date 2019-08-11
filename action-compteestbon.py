#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hermes_python.hermes import Hermes
from hermes_python.ffi.utils import MqttOptions
from hermes_python.ontology.dialogue import DialogueConfiguration
import random

INTENT_START = "abienvenu:startLeCompteEstBon"
INTENT_HOWMANY = "abienvenu:combienDeNombres"
INTENT_REPEAT = "abienvenu:repeatChallenge"
INTENT_TRYSOLUTION = "abienvenu:trySolution"
INTENT_GETOPERATION = "abienvenu:getOperation"
INTENT_STOP = "abienvenu:cancelGame"

state = {
    'started': False,
    'trying': False,
    'nbNumbers': None,
    'numbers': [],
    'trialNumbers': [],
    'target': None,
    'solution': None
}


def enable_intents(hermes, intents):
    dialogue_conf = DialogueConfiguration().enable_intents(intents)
    hermes.configure_dialogue(dialogue_conf)


def disable_intents(hermes, intents):
    dialogue_conf = DialogueConfiguration().disable_intents(intents)
    hermes.configure_dialogue(dialogue_conf)


def humaniser(nombre):
    nombre = round(nombre, 4)
    if str(nombre)[-2:] == ".0":
        nombre = int(nombre)
    return nombre


def get_combiendenombres(hermes, intent_message):
    state['nbNumbers'] = int(intent_message.slots.nbNumbers.first().value)
    disable_intents(hermes, [INTENT_HOWMANY])
    start_lecompteestbon(hermes, intent_message)


def get_operation(hermes, intent_message):
    print(list(intent_message.slots.keys()))

    if not intent_message.slots.Nombre1 or \
       not intent_message.slots.Operation or \
       not intent_message.slots.Nombre2:
        phrase = "Je n'ai pas bien compris l'opération, veuillez répéter"
        hermes.publish_continue_session(
            intent_message.session_id,
            phrase,
            [INTENT_GETOPERATION]
        )
        return

    nombre1 = humaniser(intent_message.slots.Nombre1.first().value)
    operation = intent_message.slots.Operation.first().value
    nombre2 = humaniser(intent_message.slots.Nombre2.first().value)

    if nombre1 not in state['trialNumbers']:
        phrase = "Le nombre {} ne fait pas partie de vos nombres."\
            .format(nombre1)
    elif nombre2 not in state['trialNumbers']:
        phrase = "Le nombre {} ne fait pas partie de vos nombres."\
            .format(nombre2)
    elif nombre1 % nombre2 != 0 and operation == "divisé par":
        phrase = "{} n'est pas divisible par {}".format(nombre1, nombre2)
    else:
        state['trialNumbers'].remove(nombre1)
        state['trialNumbers'].remove(nombre2)
        if operation == "plus":
            n = nombre1 + nombre2
        elif operation == "moins":
            n = nombre1 - nombre2
        elif operation == "fois":
            n = nombre1 * nombre2
        else:
            n = humaniser(nombre1 / nombre2)
        state['trialNumbers'].append(n)
        phrase = "{} {} {} égal {}.".format(nombre1, operation, nombre2, n)
        if n == state['target']:
            phrase = (
                "{} Bravo, vous avez trouvé !"
                " À quand la prochaine partie ?"
            ).format(phrase)
            disable_intents(hermes, [INTENT_GETOPERATION])
            stop_lecompteestbon(hermes, intent_message, phrase)
            return
        elif len(state['trialNumbers']) == 1:
            phrase = "{} Désolé, ça ne nous mène pas à {}."\
                .format(phrase, state['target'])
            state['trying'] = False
            disable_intents(hermes, [INTENT_GETOPERATION])
            hermes.publish_end_session(intent_message.session_id, phrase)
            return
        phrase = "{} Continuez.".format(phrase)

    hermes.publish_continue_session(
        intent_message.session_id,
        phrase,
        [INTENT_GETOPERATION]
    )


def try_solution(hermes, intent_message):
    state['trialNumbers'] = state['numbers'].copy()
    state['trying'] = True
    phrase = "Je vous écoute"
    enable_intents(hermes, [INTENT_GETOPERATION])
    hermes.publish_continue_session(
        intent_message.session_id,
        phrase,
        [INTENT_GETOPERATION]
    )


def start_lecompteestbon(hermes, intent_message):
    if state['nbNumbers'] <= 2:
        state['nbNumbers'] = 2
    if state['nbNumbers'] >= 5:
        state['nbNumbers'] = 5

    numbers = list(range(1, 11))
    numbers = numbers + numbers + [25, 50, 75, 100]
    random.shuffle(numbers)
    state['numbers'] = numbers[:state['nbNumbers']]

    target = state['numbers'][0]
    state['solution'] = "{}".format(target)
    for i in range(1, state['nbNumbers']):
        r = random.randint(1, 10)
        nb = state['numbers'][i]
        if r <= 6 and target % nb == 0:
            target = target / nb
            state['solution'] = "{} divisé par {}".format(state['solution'], nb)
        elif r <= 6 and nb % target == 0:
            target = nb / target
            state['solution'] = "{} divisé par {}".format(nb, state['solution'])
        elif r <= 3 and target > nb:
            target = target - nb
            state['solution'] = "{} moins {}".format(state['solution'], nb)
        elif r <= 3 and target < nb:
            target = nb - target
            state['solution'] = "{} moins {}".format(nb, state['solution'])
        elif r <= 8 and target * nb < 1000:
            target = target * nb
            state['solution'] = "{} fois {}".format(state['solution'], nb)
        else:
            target = target + nb
            state['solution'] = "{} + {}".format(state['solution'], nb)

    state['target'] = int(target)
    print(state['solution'])
    enable_intents(hermes, [INTENT_REPEAT, INTENT_STOP, INTENT_TRYSOLUTION])
    hermes.publish_end_session(intent_message.session_id, challenge())


def challenge():
    return "Voici vos nombres: {}. Il faut trouver: {}. Bonne chance!"\
        .format(", ".join(map(str, state['numbers'])), state['target'])


def repeat_challenge(hermes, intent_message):
    hermes.publish_end_session(intent_message.session_id, challenge())


def stop_game(hermes, intent_message):
    phrase = "La solution était {}. À bientôt.".format(state['solution'])
    stop_lecompteestbon(hermes, intent_message, phrase)


def stop_lecompteestbon(hermes, intent_message, phrase):
    state['started'] = False
    state['trying'] = False
    disable_intents(
        hermes,
        [INTENT_REPEAT, INTENT_STOP, INTENT_TRYSOLUTION]
    )
    hermes.publish_end_session(intent_message.session_id, phrase)


def start_game(hermes, intent_message):
    state['started'] = True
    if intent_message.slots.nbNumbers.first():
        state['nbNumbers'] = int(intent_message.slots.nbNumbers.first().value)
        start_lecompteestbon(hermes, intent_message)
    else:
        phrase = "Avec combien de nombres voulez-vous jouer au compte est bon?"
        enable_intents(hermes, [INTENT_HOWMANY])
        hermes.publish_continue_session(
            intent_message.session_id,
            phrase,
            [INTENT_HOWMANY]
        )


def intent_callback(hermes, intent_message):
    intent_name = intent_message.intent.intent_name
    if intent_name == INTENT_START:
        start_game(hermes, intent_message)
    elif state['started']:
        if intent_name == INTENT_HOWMANY:
            get_combiendenombres(hermes, intent_message)
        elif intent_name == INTENT_REPEAT:
            repeat_challenge(hermes, intent_message)
        elif intent_name == INTENT_STOP:
            stop_game(hermes, intent_message)
        elif intent_name == INTENT_TRYSOLUTION:
            try_solution(hermes, intent_message)
        elif intent_name == INTENT_GETOPERATION and state['trying']:
            get_operation(hermes, intent_message)


if __name__ == "__main__":
    mqtt_opts = MqttOptions()
    with Hermes(mqtt_options=mqtt_opts) as h:
        h.subscribe_intents(intent_callback).start()
