import socket
import threading
from typing import Optional

from PyQt6.QtCore import pyqtSignal, QObject

from src.protocol import TumultSocket, RequestType, ENCODING_FORMAT


class TumultClient(QObject):

    message_received = pyqtSignal((str, str))
    join_message_received = pyqtSignal((str, str))
    leave_message_received = pyqtSignal((str, str))
    disconnected = pyqtSignal()

    @staticmethod
    def client_host_address() -> str:
        return socket.gethostbyname(socket.gethostname())

    def __init__(self):
        super().__init__()
        self.server_ipv4_address: Optional[str] = None
        self.server_port: Optional[int] = None
        self.nickname: Optional[str] = None
        self.server_socket: TumultSocket = TumultSocket()

    @property
    def server_socket_address(self) -> str:
        return f"{self.server_ipv4_address}:{self.server_port}"

    def send_nickname(self):
        self.server_socket.write_nickname(self.nickname)

    def send_message(self, message: str):
        self.server_socket.write_message(self.nickname, message)

    def connect(
        self, server_ipv4_address: str, server_port: int, nickname: Optional[str]
    ) -> bool:
        self.server_ipv4_address = server_ipv4_address
        self.server_port = server_port
        self.nickname = nickname

        print(f"Attempting to connect to server {self.server_socket_address}")
        try:
            self.server_socket.connect((self.server_ipv4_address, self.server_port))
            server_thread = threading.Thread(target=self.handle_server_requests)
            server_thread.start()
            print(f"Connected to server {self.server_socket_address}")
            return True
        except TimeoutError:
            print(f"Connection to server timed out")
        except ConnectionRefusedError:
            print(f"Connection to the server was actively refused")
        except ConnectionResetError:
            print(f"Connection was forcibly closed by the server")
        except ConnectionError as error:
            print(f"Connection error occurred: {error}")

        self.disconnected.emit()
        return False

    def handle_server_requests(self):
        handling_server_requests = True
        while handling_server_requests:
            try:
                request = self.server_socket.read_request()
                if not request or not request.header:
                    continue

                match request.header.request_type:

                    case RequestType.NICKNAME:
                        self.send_nickname()

                    case RequestType.MESSAGE:
                        nickname = request.header.nickname
                        message = request.contents.decode(ENCODING_FORMAT)
                        print(f"Received from server: {nickname} says {message}")
                        self.message_received.emit(nickname, message)

                    case RequestType.JOIN_MESSAGE:
                        nickname = request.header.nickname
                        message = request.contents.decode(ENCODING_FORMAT)
                        print(f"Received from server: {nickname} joined")
                        self.join_message_received.emit(nickname, message)

                    case RequestType.LEAVE_MESSAGE:
                        nickname = request.header.nickname
                        message = request.contents.decode(ENCODING_FORMAT)
                        print(f"Received from server: {nickname} left")
                        self.leave_message_received.emit(nickname, message)

            except TimeoutError:
                print(f"Connection to server timed out")
                handling_server_requests = False
            except ConnectionResetError:
                print(f"Connection was forcibly closed by the server")
                handling_server_requests = False
            except ConnectionAbortedError:
                print(f"Connection to the server was aborted")
                handling_server_requests = False
            except ConnectionError as error:
                print(f"Connection error occurred: {error}")
                handling_server_requests = False

        self.disconnected.emit()

    def leave_server(self):
        self.server_ipv4_address = None
        self.server_port = None
        self.server_socket.close()
        self.server_socket = TumultSocket()
