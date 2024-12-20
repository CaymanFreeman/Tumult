import socket
import threading
from typing import Tuple

from src.protocol.protocol import TumultProtocol, Request


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

    @staticmethod
    def handle_incoming_message(connection: socket):
        header_contents = connection.recv(TumultProtocol.header_length_bytes).decode(
            TumultProtocol.encoding_format
        )

        if not header_contents:
            return None, None

        message_length = int(header_contents)
        message = connection.recv(message_length).decode(TumultProtocol.encoding_format)

        return header_contents, message

    def handle_client_requests(self, connection: socket, address: Tuple[str, int]):
        self.clients.append((socket, address))
        print(f"Client connected from {address[0]}:{address[1]}")
        handling_messages = True
        while handling_messages:
            try:
                request_header = connection.recv(
                    TumultProtocol.header_length_bytes
                ).decode(TumultProtocol.encoding_format)

                if not request_header:
                    continue

                match int(request_header):
                    case Request.DISCONNECT.value:
                        print(
                            f"Received disconnect request from {address[0]}:{address[1]}"
                        )
                        break
                    case Request.MESSAGE.value:
                        message_length, message = self.handle_incoming_message(
                            connection
                        )
                        if not message_length or not message:
                            continue
                        print(
                            f"Received message '{message}' from {address[0]}:{address[1]} with length {message_length}"
                        )
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
                target=self.handle_client_requests, args=(socket_connection, ip_address)
            )
            client_thread.start()
