
[[_TOC_]]

# Installation

This bot is a docker container and needs some configuration before you build it.

## Configuration
The bot requires settings in a TOML-file in `bot/config.toml` (not part of the repository).

Example config:
```toml
[server]
address = "127.0.0.1"
channel = "#test"

[bot]
botnick = "pythonbot"
ownernick = "guido"
```

## Build and run

### Build
The following line builds the docker container, 'pythonbot' is a name you choose for the bot, the tag ('latest') is optional:
```bash
docker build -t pythonbot:latest .
```
Note the dot at the end!

You only need to build when the code or config has been changed.

### Run interactively
To run the bot, use the following:
```bash
docker run pythonbot:latest
```
The name:tag (`pythonbot:latest`) needs to be the same as when you build it.

The bot writes logs to stdout, you can divert this:
```bash
# Ignore logs altogether:
docker run pythonbot:latest > /dev/null

# Append logs to a file bot.log:
docker run pythonbot:latest >> bot.log

# Append logs to a file bot.log and to stdout:
docker run pythonbot:latest | tee -a bot.log
```

The bot closes when it fails to connect initially. Otherwise it keeps running. To close the bot, hit ctrl-c.

### Run as a daemon
You can also run the bot as a daemon. Use the following line on the first run:
```bash
docker run -d --name mybot pythonbot:latest
```
Where `mybot` is a name you choose.

To stop the bot:
```bash
docker stop mybot
```

And to start subsequent runs:
```bash
docker start mybot
```

Removing the bot:
```bash
docker rm mybot
```