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


def get_topdesk_ticket_desc(number: str):
    if topdeskServer and topdeskUser and topdeskPass:
        print(f"[INFO] Lookup TOPdesk ticket {number}")
        number = number.upper()
        if number[0] == "M":
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
            # Assume number[0] == "W"
            response = requests.get(
                f"{topdeskServer}/tas/api/operatorChanges/{number}",
                auth=HTTPBasicAuth(topdeskUser, topdeskPass),
            )
            if response.status_code == 200:
                respJson = json.loads(response.text)
                return f"{number}: {respJson['requester']['branch']['name']} - {respJson['briefDescription']}"
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

ticketPattern = re.compile(r"[mMwW]\d{8}")
halloPattern = re.compile(f"(Hallo|Hoi) {nick}!?", re.IGNORECASE)

helpText = f"""Hoi, ik ben {nick}! En ik kan deze dingen:
!catfact        ik vertel een kattenfeitje van catfact.ninja;
!joke           ik vertel een mop van jokeapi.dev;
!reverse [msg]  ik keer msg om, als msg leeg is keer ik het vorige chatbericht om;
!tronald        ik citeer de cheeto via tronalddump.io.
Als je me een meldingsnummer geeft, dan geef ik de omschrijving en status."""

previousMessage = ""

for response in client.read_messages():

    if response.command == "PRIVMSG" and channel in response.receivers:

        # Keep track of the current message, this will be the next previous message
        # It is either the received message, or the bot's reply
        currentMessage = response.message

        if response.message == "!catfact":
            resp = requests.get("https://catfact.ninja/fact")
            currentMessage = client.send_all_messages(channel, resp.json()["fact"])

        elif response.message == "!hallo" or halloPattern.match(response.message):
            usernick = response.source_nick()
            if usernick:
                currentMessage = client.send_message(channel, f"Hoi {usernick}!")
            else:
                currentMessage = client.send_message(channel, "Hallo!")

        elif response.message == "!help":
            currentMessage = client.send_all_messages(channel, helpText)

        elif response.message == "!joke":
            resp = requests.get("https://v2.jokeapi.dev/joke/Any?type=single&safe-mode")
            currentMessage = client.send_all_messages(channel, resp.json()["joke"])
            print(f"[Info] Joke metadata: {resp.content}")

        elif response.message.startswith("!name "):
            msg = response.message.split(maxsplit=1)
            if len(msg) == 1 or msg[1].strip() == "":
                print(f"[Info] !name received, but no new name given")
            else:
                nick = msg[1]
                halloPattern = re.compile(f"(Hallo|Hoi) {nick}!?", re.IGNORECASE)

        elif response.message.split(maxsplit=1)[0] == "!reverse":
            msg = response.message.split(maxsplit=1)
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
            currentMessage = client.send_all_messages(channel, resp.json()["value"])
            print(f"[Info] Tronald metadata: {resp.content}")

        elif m := ticketPattern.search(response.message):
            number = m.group()
            ticketMsg = get_topdesk_ticket_desc(number)
            if ticketMsg:
                currentMessage = client.send_message(channel, ticketMsg)

        previousMessage = currentMessage
