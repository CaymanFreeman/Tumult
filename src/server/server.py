import socket
import threading
from collections import namedtuple
from dataclasses import dataclass
from enum import IntEnum
from typing import Tuple


@dataclass
class TumultProtocol:
    transport_type: IntEnum = socket.SOCK_STREAM  # TCP Stream
    address_family: IntEnum = socket.AF_INET  # IPV4
    port: int = 65535
    header_length_bytes: int = 4
    encoding_format: str = "utf-8"


class Server:

    @staticmethod
    def server_host_address() -> str:
        return socket.gethostbyname(socket.gethostname())

    def __init__(
        self, address: str = server_host_address(), port: str = TumultProtocol.port
    ):
        self.socket_address = address, port
        self.socket = socket.socket(
            type=TumultProtocol.transport_type,
            family=TumultProtocol.address_family,
        )
        self.socket.bind(self.socket_address)
        self.clients = []

    def start(self):
        print(f"Starting server at {self.socket_address[0]}:{self.socket_address[1]}")
        self.socket.listen()
        self.handle_client_connections()

    def broadcast_message(self, message: str):
        pass

    def handle_client_messages(self, connection: socket, address: Tuple[str, int]):
        print(f"Client connected from {address[0]}:{address[1]}")
        handling_messages = True
        while handling_messages:
            try:
                message_header_contents = connection.recv(
                    TumultProtocol.header_length_bytes
                ).decode(TumultProtocol.encoding_format)
                if not message_header_contents:
                    continue
                message_length = int(message_header_contents)
                message = connection.recv(message_length).decode(
                    TumultProtocol.encoding_format
                )
                print(f"Received message '{message}' from {address[0]}:{address[1]}")
                self.broadcast_message(message)
            except Exception as e:
                print(e)
                break
        connection.close()

    def handle_client_connections(self):
        handling_connections = True
        while handling_connections:
            socket_connection, ip_address = self.socket.accept()
            client_thread = threading.Thread(
                target=self.handle_client_messages, args=(socket_connection, ip_address)
            )
            client_thread.start()
