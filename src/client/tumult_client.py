"""Provides the client implementation for Tumult."""

import ipaddress
import logging
import threading
from dataclasses import dataclass
from typing import Optional

from PyQt6.QtCore import pyqtSignal, QObject

from src.shared.protocol import TumultSocket, RequestType, ENCODING_FORMAT


@dataclass
class ServerInfo:
    """Container for server connection information."""

    ipv4_address: Optional[str] = None
    port: Optional[int] = None
    socket: TumultSocket = TumultSocket()

    def __str__(self) -> str:
        """Returns a string representation of the socket address in address:port format."""
        return f"{self.ipv4_address}:{self.port}"

    @property
    def socket_address(self) -> tuple[Optional[str], Optional[int]]:
        """Returns the socket address as a tuple."""
        return self.ipv4_address, self.port

    @socket_address.setter
    def socket_address(self, socket_address: tuple[str, int]) -> None:
        """Sets the socket address with a tuple containing the IPv4 address and port."""
        self.ipv4_address, self.port = socket_address

    @property
    def address_scope(self) -> str:
        """Returns the server's IPv4 address scope."""
        if self.ipv4_address is None:
            return "unknown"
        try:
            if ipaddress.IPv4Address(self.ipv4_address).is_loopback:
                return "loopback"
            if ipaddress.IPv4Address(self.ipv4_address).is_private:
                return "private"
            if ipaddress.IPv4Address(self.ipv4_address).is_global:
                return "public"
            return "reserved"
        except ValueError:
            return "unknown"

    def connect(self) -> None:
        """Initiates a connection using the current socket and socket_address."""
        self.socket.connect(self.socket_address)


class TumultClient(QObject):
    """Client implementation for Tumult."""

    message_received = pyqtSignal((str, str))
    join_message_received = pyqtSignal(str)
    leave_message_received = pyqtSignal(str)
    disconnected = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.nickname: Optional[str] = None
        self.server: ServerInfo = ServerInfo()

    def send_nickname(self) -> None:
        """Sends the client's nickname to the server."""
        self.server.socket.write_nickname(self.nickname)

    def send_message(self, message: str) -> None:
        """Sends a chat message to the server with the client's nickname."""
        self.server.socket.write_message(self.nickname, message)

    def connect(self) -> bool:
        """Initiates the server connection and starts a request handling thread."""
        try:
            logging.info(
                "Attempting connection to server with %s address %s",
                self.server.address_scope,
                self.server,
            )
            self.server.connect()
            server_thread: threading.Thread = threading.Thread(
                target=self._handle_server_requests
            )
            server_thread.start()
            logging.info("Connected to server")
            return True
        except TimeoutError:
            logging.error("Connection to server timed out")
        except ConnectionRefusedError:
            logging.error("Connection to the server was actively refused")
        except ConnectionResetError:
            logging.error("Connection was forcibly closed by the server")
        except ConnectionError as error:
            logging.error("Connection error occurred: %s", error)

        self.disconnected.emit()
        logging.error("Connection to server %s failed", self.server)
        return False

    def _handle_server_requests(self) -> None:
        """Processes incoming server requests and emits the corresponding signals."""
        handling_server_requests: bool = True
        while handling_server_requests:
            try:
                request: TumultSocket.Request = self.server.socket.read_request()
                if not request or not request.header:
                    continue

                match request.header.request_type:

                    case RequestType.NICKNAME:
                        self.send_nickname()
                        logging.info(
                            "Server asked for nickname, provided %s", self.nickname
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
                logging.error("Connection to server timed out")
                handling_server_requests = False
            except ConnectionResetError:
                logging.error("Connection was forcibly closed by the server")
                handling_server_requests = False
            except ConnectionAbortedError:
                logging.error("Connection to the server was aborted")
                handling_server_requests = False
            except ConnectionError as error:
                logging.error("Connection error occurred: %s", error)
                handling_server_requests = False

        self.disconnected.emit()

    def leave_server(self) -> None:
        """Disconnects from the server and resets the server information."""
        self.server.ipv4_address = None
        self.server.port = None
        self.server.socket.close()
        self.server.socket = TumultSocket()
