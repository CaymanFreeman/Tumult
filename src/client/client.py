import socket

from src.server.server import Request, TumultProtocol


class Client:

    @staticmethod
    def client_host_address() -> str:
        return socket.gethostbyname(socket.gethostname())

    @staticmethod
    def pad_for_header(header_contents: bytes):
        return header_contents + (
            b" " * (TumultProtocol.header_length_bytes - len(header_contents))
        )

    # Send header describing what the incoming request will be
    def send_request_header(self, request_type: int):
        header_contents = str(request_type).encode(TumultProtocol.encoding_format)
        self.socket.send(self.pad_for_header(header_contents))

    def __init__(
        self,
        server_address: str = client_host_address(),
        port: int = TumultProtocol.port,
    ):
        self.socket_address = server_address, port
        self.socket = socket.socket(
            type=TumultProtocol.transport_type,
            family=TumultProtocol.address_family,
        )

    def connect(self):
        self.socket.connect(self.socket_address)

    # Send header before the message that describes the length of the message
    def send_message_header(self, message_length: int):
        header_contents = str(message_length).encode(TumultProtocol.encoding_format)
        self.socket.send(self.pad_for_header(header_contents))

    def send_message(self, message: str):
        self.send_request_header(Request.MESSAGE.value)
        message = message.encode(TumultProtocol.encoding_format)
        self.send_message_header(len(message))
        self.socket.send(message)

    def send_disconnect(self):
        self.send_request_header(Request.DISCONNECT.value)
