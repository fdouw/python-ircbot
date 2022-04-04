#!/usr/bin/env python

from irc import *
import json
import re
import requests
from requests.auth import HTTPBasicAuth
import toml


### Read settings   ####################################################################################################

config = toml.load("config.toml")

if "bot" in config.keys() and "botnick" in config["bot"].keys():
    nick = config["bot"]["botnick"]
else:
    nick = "bot"

if "bot" in config.keys() and "ownernick" in config["bot"].keys():
    ownernick = config["bot"]["ownernick"]
else:
    ownernick = nick

if "server" in config.keys() and "channel" in config["server"].keys():
    channel = config["server"]["channel"]
else:
    channel = "#test"

if "server" in config.keys() and "address" in config["server"].keys():
    serverAddress = config["server"]["address"]
else:
    serverAddress = "localhost"

if "topdesk" in config.keys():
    topdeskServer = (
        config["topdesk"]["server"] if "server" in config["topdesk"].keys() else None
    )
    topdeskUser = (
        config["topdesk"]["user"] if "user" in config["topdesk"].keys() else None
    )
    topdeskPass = (
        config["topdesk"]["password"]
        if "password" in config["topdesk"].keys()
        else None
    )


### Functions   ########################################################################################################


def get_topdesk_melding_desc(number):
    if topdeskUser and topdeskPass:
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

previousMessage = ""

for response in client.read_response_lines():
    # In most instances (PRIVMSGs), the fourth entry is a message,
    # splitting like this allows us to retain the spaces in the message
    data = response.strip().split(maxsplit=3)

    if data[1] == "PRIVMSG" and data[2] == channel:

        if data[3] == ":!catfact":
            resp = requests.get("https://catfact.ninja/fact")
            fact = resp.json()["fact"]
            for line in fact.splitlines():
                client.send_message(channel, line)

        elif data[3] == ":!hallo":
            client.send_message(channel, "Hoi luitjes!")

        elif data[3] == ":!help":
            client.send_message(channel, f"Hoi, ik ben {nick}! En ik kan deze dingen:")
            client.send_message(
                channel,
                "!catfact         ik vertel een kattenfeitje van catfact.ninja;",
            )
            client.send_message(
                channel, "!joke            ik vertel een mop van jokeapi.dev;"
            )
            client.send_message(
                channel,
                "!reverse [msg]   ik keer msg om, als msg leeg is keer ik het vorige chatbericht om;",
            )

        elif data[3] == ":!joke":
            resp = requests.get("https://v2.jokeapi.dev/joke/Any?type=single&safe-mode")
            joke = resp.json()["joke"]
            for line in joke.splitlines():
                client.send_message(channel, line)
            print(f"[Info] Joke metadata: {resp.content}")

        elif data[3].startswith(":!reverse"):
            # Python is weird when indexing and reversing at the same time
            # the :0:-1 drops the first character and reverses the remainder
            msg = data[3].split(maxsplit=2)
            if len(msg) >= 2:
                client.send_message(channel, msg[1][::-1])
            elif len(previousMessage) > 0:
                client.send_message(channel, previousMessage[:0:-1])
            else:
                client.send_message(channel, "Ik heb niets om te reversen :(")

        elif m := meldingPattern.search(data[3]):
            melding = m.group()
            meldingMsg = get_topdesk_melding_desc(melding)
            if meldingMsg:
                client.send_message(channel, meldingMsg)

        previousMessage = data[3]
