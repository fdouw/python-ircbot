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
        for response in self.read_response_lines():
            response = response.split()

            if response[1] == "001":
                self.socket.send(bytes(f"JOIN {channel}\n", "UTF-8"))
                print(f"Joined channel {channel}")
                return True

            elif response[1] == "ERROR":
                print(
                    f"[Error] Received an error while connecting: {' '.join(response[2:])}"
                )
                print(f"Closing connection")
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
                return False

    def read_response_lines(self, processPing=True):
        # IRC responses / messages are deliminated by line endings, but socket doesn't know that, so we will have to
        # keep track of those our selves.
        # The leftover is the start of the next response, so we need to remember that.
        leftover = ""

        while True:
            message = leftover
            splitIndex = message.find("\n")

            while splitIndex == -1:
                message += self.socket.recv(2048).decode("UTF-8")
                splitIndex = message.find("\n")

            leftover = message[splitIndex + 1 :]
            message = message[:splitIndex]

            print(f"[Received] {message}")
            if processPing and message.startswith("PING"):
                self.socket.send(
                    bytes(f"PONG {message.split(maxsplit=3)[1]}\n", "UTF-8")
                )
                continue

            yield message
