import re
import socket


class IRC:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def send_message(self, channel, msg):
        print(f"Sending message: '{msg}'")
        self.socket.send(bytes(f"PRIVMSG {channel} :{msg}\n", "UTF-8"))

    def connect(self, nick, channel, server, port=6667):
        username = nick
        realname = nick
        self.socket.connect((server, port))
        self.socket.send(bytes(f"NICK {nick}\n", "UTF-8"))
        self.socket.send(bytes(f"USER {username} 0 * :{realname}\n", "UTF-8"))

        # Wait for the 001 response from the server, indicating that we have registered
        for response in self.read_messages():
            if response.command == "001":
                self.socket.send(bytes(f"JOIN {channel}\n", "UTF-8"))
                print(f"Joined channel {channel}")
                return True

            elif response.command == "ERROR":
                print(
                    f"[Error] Received an error while connecting: {response.parameters}"
                )
                print(f"Closing connection")
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
                return False

    def read_messages(self, answerPing=True, filter=None):
        """
        Returns a generator that passes on any messages received, as IrcMessage objects.
        param   answerPing  if True, answer PING messages and do not pass these messages on;
        param   filter      only pass on messages whose command is in filter, pass on all messages if filter is None.
                            Note: answerPing filters out PING messages regardless of filter.
        """
        # IRC responses / messages are deliminated by line endings, but socket doesn't know that, so we will have to
        # keep track of those our selves.
        # The leftover is the start of the next response, so we need to remember that.
        leftover = ""

        while True:
            current = leftover
            splitIndex = current.find("\n")

            while splitIndex == -1:
                current += self.socket.recv(2048).decode("UTF-8")
                splitIndex = current.find("\n")

            leftover = current[splitIndex + 1 :]
            current = current[:splitIndex]

            print(f"[Received] {current}")
            message = IrcMessage.parse_message(current)
            if answerPing and message.command == "PING":
                self.socket.send(bytes(f"PONG {message.parameters}\n", "UTF-8"))
                continue
            if filter == None or message.command in filter:
                yield message


class IrcMessage:
    def __init__(self, rawmessage, tags: dict, source, command, parameters):
        self.rawmessage = rawmessage
        self.tags = tags
        self.source = source
        self.command = command
        self.parameters = parameters

    @staticmethod
    def parse_message(rawmsg: str):
        # The : before the prefix is required, but InpIRCd seemingly misses it during the MotD.
        # I'm keeping it optional here for compatibility.
        msgPatternMatch = re.fullmatch(
            r"(@[^ ]+ )?(:?[^ ]+ )?([0-9]{3}|[A-Z]+) (.*)", rawmsg.strip()
        )
        if not msgPatternMatch:
            raise ValueError(f"Invalid message: {rawmsg}")
        tags, source, command, parameters = msgPatternMatch.groups()

        # Process some shared properties of irc messages
        tagDict = dict()
        if tags:
            for t in tags[1:].split(";"):
                # Assumes valid formatting!
                k, v = t.split("=", 1)
                tagDict[k] = v

        if source:
            source = source[1:]

        message = IrcMessage(rawmsg, tagDict, source, command, parameters)

        # Process properties specific to certain types of messages
        if command == "PRIVMSG":
            rec, msg = parameters.split(" ", 1)
            message.receivers = rec.split(",")
            message.message = msg.lstrip(":")

        return message

    def source_nick(self):
        if self.source:
            nickPatternMatch = re.match(r"[a-z][-a-z0-9`^{}[\]\\]*", self.source, re.I)
            return nickPatternMatch.group() if nickPatternMatch else None
        return None
