import atexit
import socket
import threading

from src.protocol.protocol import TumultProtocol


class Client:

    @staticmethod
    def client_host_address() -> str:
        return socket.gethostbyname(socket.gethostname())

    def __init__(
        self,
        server_address: str = client_host_address(),
        server_port: int = TumultProtocol.default_port,
    ):
        self.server_socket_address = server_address, server_port
        self.server_connection = socket.socket(
            type=TumultProtocol.transport_type,
            family=TumultProtocol.address_family,
        )

    @property
    def is_connected(self) -> bool:
        try:
            self.server_connection.getpeername()
            return True
        except OSError:
            return False

    def connect(self):
        server_address, server_port = self.server_socket_address
        try:
            print(f"Attempting to connect to server {server_address}:{server_port}")
            self.server_connection.connect(self.server_socket_address)
            server_thread = threading.Thread(target=self.handle_server_requests)
            server_thread.start()
            print(f"Connected to server {server_address}:{server_port}")
        except ConnectionError as error:
            print(f"Connection failed: {error}")
        except OSError as error:
            print(f"Connection failed: {error}")

    def send_message(self, message: str):
        TumultProtocol.send_message(self.server_connection, message)

    def send_disconnect_request(self):
        TumultProtocol.send_request_header(
            self.server_connection, TumultProtocol.Request.DISCONNECT
        )

    def disconnect(self):
        self.send_disconnect_request()
        self.server_connection.close()

    def handle_server_requests(self):
        handling_requests = True
        while handling_requests:
            try:
                request = TumultProtocol.handle_incoming_request(self.server_connection)

                if not request:
                    continue

                if int(request) == TumultProtocol.Request.MESSAGE.value:
                    message_length, message = TumultProtocol.handle_incoming_message(
                        self.server_connection
                    )
                    if not message_length or not message:
                        continue
                    print(
                        f"Received message from server: '{message}' ({message_length} bytes)"
                    )
            except ConnectionAbortedError:
                print(f"Disconnected from server")
                return
            except ConnectionError as error:
                print(f"Disconnected from server: {error}")
                return
