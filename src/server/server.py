import socket
import threading
from typing import Tuple

from src.protocol import TumultProtocol


class Server:

    @staticmethod
    def server_host_address() -> str:
        return socket.gethostbyname(socket.gethostname())

    def __init__(
        self,
        address: str = server_host_address(),
        port: str = TumultProtocol.default_port,
    ):
        self.socket_address = address, port
        self.socket = TumultProtocol.socket()
        self.socket.bind(self.socket_address)
        self.client_connections = []
        self.nicknames = {}
        self.message_history = []

    def start(self):
        address, port = self.socket_address
        print(f"Starting server at {address}:{port}")
        self.socket.listen()
        self.handle_client_connections()

    def broadcast_message(self, message: str):
        self.message_history.append(message)
        print(f"Sending message '{message}' to {list(self.nicknames.values())}")
        for client_connection in self.client_connections:
            TumultProtocol.send_string(
                client_connection, TumultProtocol.Request.MESSAGE, message
            )

    def send_message_history(self, client: Tuple[socket, Tuple[str, int]]):
        client_connection, _ = client
        for message in self.message_history:
            TumultProtocol.send_string(
                client_connection, TumultProtocol.Request.MESSAGE, message
            )

    def disconnect_client(self, client: Tuple[socket, Tuple[str, int]]):
        client_connection, client_socket_address = client
        self.client_connections.remove(client_connection)
        if client_socket_address in self.nicknames.keys():
            del self.nicknames[client_socket_address]
        client_connection.close()

    def get_nickname(self, client: Tuple[socket, Tuple[str, int]]) -> str:
        client_connection, client_socket_address = client
        client_ip_address, client_port = client_socket_address
        if client_socket_address not in self.nicknames.keys():
            nickname = "User" + str(
                self.client_connections.index(client_connection) + 1
            )
            print(
                f"Giving default nickname {nickname} to client {client_ip_address}:{client_port}"
            )
            self.nicknames[client_socket_address] = nickname
        return self.nicknames[client_socket_address]

    def handle_client_requests(
        self, client_connection: socket, client_socket_address: Tuple[str, int]
    ):
        client = client_connection, client_socket_address
        client_ip_address, client_port = client_socket_address
        self.client_connections.append(client_connection)
        print(f"Client connected from {client_ip_address}:{client_port}")
        if self.message_history:
            print(
                f"Sending message history to client {client_ip_address}:{client_port}"
            )
            self.send_message_history(client)
            print(
                f"Finished sending messages to client {client_ip_address}:{client_port}"
            )
        handling_requests = True
        while handling_requests:
            try:
                request = TumultProtocol.handle_incoming_request(client_connection)
                if not request:
                    continue

                match request:
                    case TumultProtocol.Request.NICKNAME:
                        nickname = TumultProtocol.handle_incoming_string(
                            client_connection
                        )
                        if not nickname:
                            continue

                        print(
                            f"Received nickname request of '{nickname}' from client {client_ip_address}:{client_port}"
                        )
                        self.nicknames[client_socket_address] = nickname
                    case TumultProtocol.Request.MESSAGE:
                        message = TumultProtocol.handle_incoming_string(
                            client_connection
                        )
                        if not message:
                            continue

                        print(
                            f"Received message from client {client_ip_address}:{client_port}: {message}"
                        )
                        self.broadcast_message(
                            f"[{self.get_nickname(client)}] {message}"
                        )
            except TimeoutError as error:
                print(
                    f"Connection with client {client_ip_address}:{client_port} timed out: {error}"
                )
                handling_requests = False
            except ConnectionResetError:
                print(
                    f"Connection with client {client_ip_address}:{client_port} was forcibly closed by them"
                )
                handling_requests = False
            except ConnectionAbortedError as error:
                print(
                    f"Connection with client {client_ip_address}:{client_port} was aborted: {error}"
                )
                handling_requests = False
            except ConnectionError as error:
                print(
                    f"Connection with client {client_ip_address}:{client_port} experienced an error: {error}"
                )
                handling_requests = False
        self.disconnect_client(client)

    def handle_client_connections(self):
        handling_connections = True
        while handling_connections:
            socket_connection, ip_address = self.socket.accept()
            client_thread = threading.Thread(
                target=self.handle_client_requests, args=(socket_connection, ip_address)
            )
            client_thread.start()
