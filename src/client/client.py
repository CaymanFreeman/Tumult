import logging
import threading
from typing import Optional

from PyQt6.QtCore import pyqtSignal, QObject

from src.shared.protocol import TumultSocket, RequestType, ENCODING_FORMAT


class TumultClient(QObject):

    message_received = pyqtSignal((str, str))
    join_message_received = pyqtSignal(str)
    leave_message_received = pyqtSignal(str)
    disconnected = pyqtSignal()

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
        try:
            self.server_socket.connect((self.server_ipv4_address, self.server_port))
            server_thread = threading.Thread(target=self.handle_server_requests)
            server_thread.start()
            logging.info(f"Connected to server {self.server_socket_address}")
            return True
        except TimeoutError:
            logging.error(f"Connection to server timed out")
        except ConnectionRefusedError:
            logging.error(f"Connection to the server was actively refused")
        except ConnectionResetError:
            logging.error(f"Connection was forcibly closed by the server")
        except ConnectionError as error:
            logging.error(f"Connection error occurred: {error}")

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
                        self.message_received.emit(nickname, message)

                    case RequestType.JOIN_MESSAGE:
                        nickname = request.header.nickname
                        self.join_message_received.emit(nickname)

                    case RequestType.LEAVE_MESSAGE:
                        nickname = request.header.nickname
                        self.leave_message_received.emit(nickname)

            except TimeoutError:
                logging.error(f"Connection to server timed out")
                handling_server_requests = False
            except ConnectionResetError:
                logging.error(f"Connection was forcibly closed by the server")
                handling_server_requests = False
            except ConnectionAbortedError:
                logging.error(f"Connection to the server was aborted")
                handling_server_requests = False
            except ConnectionError as error:
                logging.error(f"Connection error occurred: {error}")
                handling_server_requests = False

        self.disconnected.emit()

    def leave_server(self):
        self.server_ipv4_address = None
        self.server_port = None
        self.server_socket.close()
        self.server_socket = TumultSocket()
