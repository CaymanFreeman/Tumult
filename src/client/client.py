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
        port: int = TumultProtocol.port,
    ):
        self.server_socket_address = server_address, port
        self.server_connection = socket.socket(
            type=TumultProtocol.transport_type,
            family=TumultProtocol.address_family,
        )

    def connect(self):
        self.server_connection.connect(self.server_socket_address)
        server_thread = threading.Thread(target=self.handle_server_requests)
        server_thread.start()

    def send_message(self, message: str):
        TumultProtocol.send_message(self.server_connection, message)

    def send_disconnect(self):
        TumultProtocol.send_request_header(
            self.server_connection, TumultProtocol.Request.DISCONNECT
        )

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
            except Exception as e:
                print(e)
                break
