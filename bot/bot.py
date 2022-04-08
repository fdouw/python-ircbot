#!/usr/bin/env python

from irc import *
import json
import re
import requests
from requests.auth import HTTPBasicAuth
import toml


### Read settings   ####################################################################################################


def get_config_item(config, item, default=None):
    result = config
    for key in item:
        if key in result:
            result = result[key]
        else:
            return default
    return result


config = toml.load("config.toml")

nick = get_config_item(config, ["bot", "botnick"], "bot")
owernick = get_config_item(config, ["bot", "ownernick"], nick)
channel = get_config_item(config, ["server", "channel"], "#test")
serverAddress = get_config_item(config, ["server", "address"], "localhost")
topdeskServer = get_config_item(config, ["topdesk", "server"])
topdeskUser = get_config_item(config, ["topdesk", "user"])
topdeskPass = get_config_item(config, ["topdesk", "password"])


### Functions   ########################################################################################################


def get_topdesk_melding_desc(number):
    if topdeskServer and topdeskUser and topdeskPass:
        print(f"[INFO] Lookup TOPdesk call {number}")
        response = requests.get(
            f"{topdeskServer}/tas/api/incidents/number/{number}",
            auth=HTTPBasicAuth(topdeskUser, topdeskPass),
        )
        if response.status_code == 200:
            respJson = json.loads(response.text)
            return f"{number}: {respJson['callerBranch']['name']} - {respJson['briefDescription']} ({respJson['processingStatus']['name']})"
        else:
            return None
    else:
        print("[INFO] No credentials for TOPdesk, cannot query for call information")


### Set up IRC   #######################################################################################################

client = IRC()
if not client.connect(nick, channel, serverAddress):
    input("Bot could not connect to server, press any key to exit.")
    exit()


### Run bot   ##########################################################################################################

meldingPattern = re.compile(r"[mM]\d{8}")
halloPattern = re.compile(f"(Hallo|Hoi) {nick}!?", re.IGNORECASE)

previousMessage = ""

for response in client.read_messages():

    if response.command == "PRIVMSG" and channel in response.receivers:

        # Keep track of the current message, this will be the next previous message
        # It is either the received message, or the bot's reply
        currentMessage = response.message

        if response.message == "!catfact":
            resp = requests.get("https://catfact.ninja/fact")
            fact = resp.json()["fact"]
            for line in fact.splitlines():
                currentMessage = client.send_message(channel, line)

        elif response.message == "!hallo" or halloPattern.match(response.message):
            usernick = response.source_nick()
            if usernick:
                currentMessage = client.send_message(channel, f"Hoi {usernick}!")
            else:
                currentMessage = client.send_message(channel, "Hallo!")

        elif response.message == "!help":
            currentMessage = client.send_message(
                channel, f"Hoi, ik ben {nick}! En ik kan deze dingen:"
            )
            currentMessage = client.send_message(
                channel,
                "!catfact         ik vertel een kattenfeitje van catfact.ninja;",
            )
            currentMessage = client.send_message(
                channel, "!joke            ik vertel een mop van jokeapi.dev;"
            )
            currentMessage = client.send_message(
                channel,
                "!reverse [msg]   ik keer msg om, als msg leeg is keer ik het vorige chatbericht om;",
            )

        elif response.message == "!joke":
            resp = requests.get("https://v2.jokeapi.dev/joke/Any?type=single&safe-mode")
            joke = resp.json()["joke"]
            for line in joke.splitlines():
                currentMessage = client.send_message(channel, line)
            print(f"[Info] Joke metadata: {resp.content}")

        elif response.message.split(maxsplit=1)[0] == "!reverse":
            msg = response.message.split(maxsplit=2)
            if len(msg) >= 2:
                currentMessage = client.send_message(channel, msg[1][::-1])
            elif len(previousMessage) > 0:
                currentMessage = client.send_message(channel, previousMessage[::-1])
            else:
                currentMessage = client.send_message(
                    channel, "Ik heb niets om te reversen :("
                )

        elif response.message == "!tronald":
            resp = requests.get("https://tronalddump.io/random/quote")
            joke = resp.json()["value"]
            for line in joke.splitlines():
                currentMessage = client.send_message(channel, line)
            print(f"[Info] Tronald metadata: {resp.content}")

        elif m := meldingPattern.search(response.message):
            melding = m.group()
            meldingMsg = get_topdesk_melding_desc(melding)
            if meldingMsg:
                currentMessage = client.send_message(channel, meldingMsg)

        previousMessage = currentMessage
