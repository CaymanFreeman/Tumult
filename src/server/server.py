import logging
import threading
from dataclasses import dataclass
from typing import Optional, Tuple

from src.shared.protocol import (
    TumultSocket,
    RequestType,
    ENCODING_FORMAT,
)


@dataclass
class TumultClient:
    ipv4_address: str
    port: int
    socket: TumultSocket
    nickname: Optional[str] = None

    def __str__(self):
        return f"{self.ipv4_address}:{self.port}"

    @property
    def socket_address(self) -> Tuple[str, int]:
        return self.ipv4_address, self.port


@dataclass
class Message:
    nickname: str
    contents: str
    message_type: RequestType = RequestType.MESSAGE


class TumultServer:

    def __init__(self, ipv4_address: str, port: int):
        self.ipv4_address: str = ipv4_address
        self.port: int = port
        self.socket: TumultSocket = TumultSocket()
        self.clients: list[TumultClient] = []
        self.message_history: list[Message] = []

        try:
            self.socket.bind((ipv4_address, port))
        except Exception as error:
            logging.error(
                f"An error occurred while binding socket ({ipv4_address}, {port}): {error}"
            )

    def __str__(self):
        return f"{self.ipv4_address}:{self.port}"

    @property
    def socket_address(self) -> Tuple[str, int]:
        return self.ipv4_address, self.port

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
        logging.info(f"Listening at {self}")
        self.socket.listen()
        self.handle_client_connections()

    def broadcast_message(self, nickname: str, contents: str):
        message = Message(nickname, contents, RequestType.MESSAGE)
        self.message_history.append(message)
        logging.info(f"{message.nickname} says {message.contents}")
        for client_socket in self.client_sockets:
            client_socket.write_message(message.nickname, message.contents)

    def broadcast_join_message(self, nickname: str):
        message = Message(nickname, "joined", RequestType.JOIN_MESSAGE)
        self.message_history.append(message)
        logging.info(f"{nickname} joined")
        for client_socket in self.client_sockets:
            client_socket.write_join_message(nickname)

    def broadcast_leave_message(self, nickname: str):
        message = Message(nickname, "left", RequestType.LEAVE_MESSAGE)
        self.message_history.append(message)
        logging.info(f"{nickname} left")
        for client_socket in self.client_sockets:
            client_socket.write_leave_message(nickname)

    def send_message_history(self, client: TumultClient):
        client_socket = client.socket
        for message in self.message_history:
            match message.message_type:
                case RequestType.MESSAGE:
                    client_socket.write_message(message.nickname, message.contents)
                case RequestType.JOIN_MESSAGE:
                    client_socket.write_join_message(message.nickname)
                case RequestType.LEAVE_MESSAGE:
                    client_socket.write_leave_message(message.nickname)

    @staticmethod
    def request_nickname(client: TumultClient):
        client.socket.write_nickname(client.nickname)

    def wait_for_nickname(self, client: TumultClient):
        nickname_request = client.socket.wait_for_request(RequestType.NICKNAME)

        if nickname_request.header.nickname is None:
            self.generate_nickname(client)
        else:
            client.nickname = nickname_request.header.nickname
        self.broadcast_join_message(client.nickname)

    def disconnect_client(self, client: TumultClient):
        self.clients.remove(client)
        if client.socket:
            client.socket.close()
        self.broadcast_leave_message(client.nickname)

        logging.info(f"Client list updated to {self.client_ipv4_addresses}")

    def generate_nickname(self, client: TumultClient):
        client.nickname = "User" + str(self.clients.index(client) + 1)
        logging.info(f"Generated nickname {client.nickname} for client {client}")

    def handle_client_requests(self, client: TumultClient):
        logging.info(f"Client connected from {client}")
        self.clients.append(client)
        logging.info(f"Client list updated to {self.client_ipv4_addresses}")
        logging.info(f"Sending message history to client {client}")
        self.send_message_history(client)

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
                        self.broadcast_message(client.nickname, message)

            except TimeoutError:
                logging.info(f"Connection with client {client} timed out")
                handling_requests = False
            except ConnectionResetError:
                logging.info(
                    f"Connection with client {client} was forcibly closed by them"
                )
                handling_requests = False
            except ConnectionAbortedError:
                logging.info(f"Connection with client {client} was aborted")
                handling_requests = False
            except ConnectionError as error:
                logging.error(
                    f"Connection with client {client} experienced an error: {error}"
                )
                handling_requests = False
            except Exception as error:
                logging.error(
                    f"An unknown error occurred with client {client}: {error}"
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
