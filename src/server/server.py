import threading
from dataclasses import dataclass
from typing import Optional

from src.protocol import TumultSocket, RequestType, ENCODING_FORMAT


@dataclass
class TumultClient:
    ipv4_address: str
    port: int
    socket: TumultSocket
    nickname: Optional[str] = None

    @property
    def socket_address(self) -> str:
        return f"{self.ipv4_address}:{self.port}"


@dataclass
class Message:
    nickname: str
    contents: str
    message_type: RequestType = RequestType.MESSAGE


class TumultServer:

    JOIN_MESSAGE: str = "has joined the server"
    LEAVE_MESSAGE: str = "has left the server"

    def __init__(self, ipv4_address: str, port: int):
        self.ipv4_address: str = ipv4_address
        self.port: int = port
        self.socket: TumultSocket = TumultSocket()
        self.clients: list[TumultClient] = []
        self.message_history: list[Message] = []

        self.socket.bind((ipv4_address, port))

    @property
    def socket_address(self) -> str:
        return f"{self.ipv4_address}:{self.port}"

    @property
    def client_sockets(self) -> list[TumultSocket]:
        client_sockets = []
        for client in self.clients:
            client_sockets.append(client.socket)
        return client_sockets

    @property
    def client_nicknames(self) -> list[str]:
        client_nicknames = []
        for client in self.clients:
            client_nicknames.append(client.nickname)
        return client_nicknames

    @property
    def client_ipv4_addresses(self):
        client_ipv4_addresses = []
        for client in self.clients:
            client_ipv4_addresses.append(client.ipv4_address)
        return client_ipv4_addresses

    def start(self):
        print(f"Starting server at {self.socket_address}")
        self.socket.listen()
        self.handle_client_connections()

    def broadcast_message(self, nickname: str, contents: str):
        message = Message(nickname, contents, RequestType.MESSAGE)
        self.message_history.append(message)
        print(
            f"Broadcasting message '{message.nickname} says {message.contents}' to {list(self.client_nicknames)}"
        )
        for client_socket in self.client_sockets:
            client_socket.write_message(message.nickname, message.contents)

    def broadcast_join_message(self, nickname: str):
        message = Message(nickname, self.JOIN_MESSAGE, RequestType.JOIN_MESSAGE)
        self.message_history.append(message)
        print(
            f"Broadcasting join message for {nickname} to {list(self.client_nicknames)}"
        )
        for client_socket in self.client_sockets:
            client_socket.write_join_message(nickname, message.contents)

    def broadcast_leave_message(self, nickname: str):
        message = Message(nickname, self.LEAVE_MESSAGE, RequestType.LEAVE_MESSAGE)
        self.message_history.append(message)
        print(
            f"Broadcasting leave message for {nickname} to {list(self.client_nicknames)}"
        )
        for client_socket in self.client_sockets:
            client_socket.write_leave_message(nickname, message.contents)

    def send_message_history(self, client: TumultClient):
        client_socket = client.socket
        for message in self.message_history:
            match message.message_type:
                case RequestType.MESSAGE:
                    client_socket.write_message(message.nickname, message.contents)
                case RequestType.JOIN_MESSAGE:
                    client_socket.write_join_message(message.nickname, message.contents)
                case RequestType.LEAVE_MESSAGE:
                    client_socket.write_leave_message(
                        message.nickname, message.contents
                    )

    @staticmethod
    def request_nickname(client: TumultClient):
        client.socket.write_nickname(client.nickname)

    def wait_for_nickname(self, client: TumultClient):
        waiting_for_nickname = True
        while waiting_for_nickname:
            request = client.socket.read_request()
            if request and request.header:
                if request.header.request_type == RequestType.NICKNAME:
                    if request.header.nickname is None:
                        self.generate_nickname(client)
                        waiting_for_nickname = False
                    else:
                        client.nickname = request.header.nickname
                        waiting_for_nickname = False
                    self.broadcast_join_message(client.nickname)

    def disconnect_client(self, client: TumultClient):
        self.clients.remove(client)
        if client.socket:
            client.socket.close()
        self.broadcast_leave_message(client.nickname)

        print(f"Updated client list: {self.client_ipv4_addresses}")

    def generate_nickname(self, client: TumultClient):
        client.nickname = "User" + str(self.clients.index(client) + 1)
        print(
            f"Generated nickname {client.nickname} for client {client.socket_address}"
        )

    def handle_client_requests(self, client: TumultClient):
        self.clients.append(client)
        print(f"Client connected from {client.socket_address}")
        print(f"Updated client list: {self.client_ipv4_addresses}")
        if self.message_history:
            print(f"Sending message history to client {client.socket_address}")
            self.send_message_history(client)
            print(f"Finished sending messages to client {client.socket_address}")

        self.request_nickname(client)
        self.wait_for_nickname(client)

        handling_requests = True
        while handling_requests:
            try:
                request = client.socket.read_request()
                if not request or not request.header:
                    continue

                match request.header.request_type:

                    case RequestType.NICKNAME:
                        client.nickname = request.header.nickname

                    case RequestType.MESSAGE:
                        message = request.contents.decode(ENCODING_FORMAT)
                        print(
                            f"Received message from client {client.socket_address}: {message}"
                        )
                        self.broadcast_message(client.nickname, message)

            except TimeoutError:
                print(f"Connection with client {client.socket_address} timed out")
                handling_requests = False
            except ConnectionResetError:
                print(
                    f"Connection with client {client.socket_address} was forcibly closed by them"
                )
                handling_requests = False
            except ConnectionAbortedError:
                print(f"Connection with client {client.socket_address} was aborted")
                handling_requests = False
            except ConnectionError as error:
                print(
                    f"Connection with client {client.socket_address} experienced an error: {error}"
                )
                handling_requests = False
            except Exception as error:
                print(
                    f"An unknown error occurred with client {client.socket_address}: {error}"
                )
                handling_requests = False
        self.disconnect_client(client)

    def handle_client_connections(self):
        handling_connections = True
        while handling_connections:
            client_socket, client_socket_address = self.socket.accept()
            client_ipv4_address, client_port = client_socket_address
            client_thread = threading.Thread(
                target=self.handle_client_requests,
                args=[
                    TumultClient(
                        ipv4_address=client_ipv4_address,
                        port=client_port,
                        socket=TumultSocket.from_socket(client_socket),
                    )
                ],
            )
            client_thread.start()
