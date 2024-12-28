import logging
import re
import threading
from dataclasses import dataclass
from typing import Optional, Tuple

from PyQt6.QtCore import pyqtSignal, QObject

from src.shared.protocol import TumultSocket, RequestType, ENCODING_FORMAT

# IPv4 Regex from Danail Gabenski
# https://stackoverflow.com/questions/5284147/validating-ipv4-addresses-with-regexp
IPV4_PATTERN: str = r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$"
PORT_PATTERN: str = (
    r"^([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$"
)


@dataclass
class TumultServer:
    ipv4_address: Optional[str] = None
    port: Optional[int] = None
    socket: TumultSocket = TumultSocket()

    def __str__(self):
        return f"{self.ipv4_address}:{self.port}"

    @property
    def socket_address(self) -> Tuple[str, int]:
        return self.ipv4_address, self.port

    @staticmethod
    def valid_socket_address(socket_address: Tuple[str, int]) -> bool:
        ipv4_address, port = socket_address
        logging.info(f"Validating socket address {ipv4_address}:{port}")
        if not bool(re.match(IPV4_PATTERN, ipv4_address)) or not bool(
            re.match(PORT_PATTERN, str(port))
        ):
            raise ValueError(socket_address)
        return True

    @socket_address.setter
    def socket_address(self, value: Tuple[str, int]):
        if self.valid_socket_address(value):
            self.ipv4_address = value[0]
            self.port = value[1]

    def connect(self):
        self.socket.connect(self.socket_address)


class TumultClient(QObject):

    message_received = pyqtSignal((str, str))
    join_message_received = pyqtSignal(str)
    leave_message_received = pyqtSignal(str)
    disconnected = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.nickname: Optional[str] = None
        self.server: TumultServer = TumultServer()

    def send_nickname(self):
        self.server.socket.write_nickname(self.nickname)

    def send_message(self, message: str):
        self.server.socket.write_message(self.nickname, message)

    def connect(self) -> bool:
        try:
            logging.info(f"Attempting connection with server")
            self.server.connect()
            server_thread = threading.Thread(target=self.handle_server_requests)
            server_thread.start()
            logging.info(f"Connected to server {self.server}")
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
        logging.error(f"Connection to server {self.server} failed")
        return False

    def handle_server_requests(self):
        handling_server_requests = True
        while handling_server_requests:
            try:
                request = self.server.socket.read_request()
                if not request or not request.header:
                    continue

                match request.header.request_type:

                    case RequestType.NICKNAME:
                        self.send_nickname()
                        logging.info(
                            f"Server asked for nickname, provided {self.nickname}"
                        )

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
        self.server.ipv4_address = None
        self.server.port = None
        self.server.socket.close()
        self.server.socket = TumultSocket()
