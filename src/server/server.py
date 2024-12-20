import socket
import threading
from typing import Tuple

from src.protocol.protocol import TumultProtocol


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
        self.socket = socket.socket(
            type=TumultProtocol.transport_type,
            family=TumultProtocol.address_family,
        )
        self.socket.bind(self.socket_address)
        self.clients = []

    @property
    def client_connections(self) -> list[socket]:
        client_connections = []
        for client in self.clients:
            client_connections.append(client[0])
        return client_connections

    @property
    def client_socket_addresses(self) -> list[Tuple[str, int]]:
        client_socket_addresses = []
        for client in self.clients:
            client_socket_addresses.append(client[1])
        return client_socket_addresses

    @property
    def client_socket_address_strs(self) -> list[str]:
        client_socket_address_strs = []
        for client_socket_address in self.client_socket_addresses:
            client_ip_address, client_port = client_socket_address
            client_socket_address_strs.append(f"{client_ip_address}:{client_port}")
        return client_socket_address_strs

    def start(self):

        print(f"Starting server at {self.socket_address[0]}:{self.socket_address[1]}")
        self.socket.listen()
        self.handle_client_connections()

    def broadcast_message(self, message: str):
        print(
            f"Sending message '{message}' ({len(message.encode(TumultProtocol.encoding_format))} bytes) to clients {self.client_socket_address_strs}"
        )
        for client_connection in self.client_connections:
            TumultProtocol.send_message(client_connection, message)

    def disconnect_client(self, client: Tuple[socket, Tuple[str, int]]):
        client_connection, client_socket_address = client
        client_ip_address, client_port = client_socket_address
        client_connection.close()
        self.clients.remove(client)
        print(f"Client {client_ip_address}:{client_port} disconnected")

    def handle_client_requests(
        self, client_connection: socket, client_socket_address: Tuple[str, int]
    ):
        client = client_connection, client_socket_address
        client_ip_address, client_port = client_socket_address
        self.clients.append(client)
        print(f"Client connected from {client_ip_address}:{client_port}")
        handling_requests = True
        while handling_requests:
            try:
                request = TumultProtocol.handle_incoming_request(client_connection)

                if not request:
                    continue

                match int(request):
                    case TumultProtocol.Request.DISCONNECT.value:
                        print(
                            f"Received disconnect request from client {client_ip_address}:{client_port}"
                        )
                        self.disconnect_client(client)
                        return
                    case TumultProtocol.Request.MESSAGE.value:
                        message_length, message = (
                            TumultProtocol.handle_incoming_message(client_connection)
                        )
                        if not message_length or not message:
                            continue
                        print(
                            f"Received message from client {client_ip_address}:{client_port}: '{message}' ({message_length} bytes)"
                        )
                        self.broadcast_message(f"{client_ip_address} | {message}")
            except ConnectionError:
                self.disconnect_client(client)
                return

    def handle_client_connections(self):
        handling_connections = True
        while handling_connections:
            socket_connection, ip_address = self.socket.accept()
            client_thread = threading.Thread(
                target=self.handle_client_requests, args=(socket_connection, ip_address)
            )
            client_thread.start()
