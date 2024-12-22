import socket
import threading

from PyQt6.QtCore import pyqtSignal, QObject

from src.protocol import TumultProtocol


class Client(QObject):

    message_received = pyqtSignal(str)

    @staticmethod
    def client_host_address() -> str:
        return socket.gethostbyname(socket.gethostname())

    def __init__(self):
        super().__init__()
        self.server_socket_address = None
        self.server_connection = TumultProtocol.socket()

    def connect(self) -> bool:
        server_address, server_port = self.server_socket_address
        print(f"Attempting to connect to server {server_address}:{server_port}")
        try:
            self.server_connection.connect(self.server_socket_address)
            server_thread = threading.Thread(target=self.handle_server_requests)
            server_thread.start()
            print(f"Connected to server {server_address}:{server_port}")
            return True
        except TimeoutError as error:
            print(f"Connection to server timed out: {error}")
        except ConnectionRefusedError:
            print(f"Connection to the server was actively refused")
        except ConnectionResetError:
            print(f"Connection was forcibly closed by the server")
        except ConnectionError as error:
            print(f"Connection error occurred: {error}")
        except Exception as error:
            print(f"An unexpected error occurred: {error}")
        return False

    def send_message(self, message: str):
        TumultProtocol.send_string(
            self.server_connection, TumultProtocol.Request.MESSAGE, message
        )
        print(f"Sending message to server: {message}")

    def send_nickname(self, nickname: str):
        TumultProtocol.send_string(
            self.server_connection, TumultProtocol.Request.NICKNAME, nickname
        )

    def close_socket(self):
        self.server_socket_address = None
        self.server_connection.close()
        self.server_connection = TumultProtocol.socket()

    def handle_server_requests(self):
        handling_server_requests = True
        while handling_server_requests:
            try:
                request = TumultProtocol.handle_incoming_request(self.server_connection)
                if not request:
                    continue

                if request == TumultProtocol.Request.MESSAGE:
                    message = TumultProtocol.handle_incoming_string(
                        self.server_connection
                    )
                    if not message:
                        continue

                    print(f"Received message from server: '{message}'")
                    self.message_received.emit(message)
            except ConnectionResetError:
                print(f"Connection was forcibly closed by the server")
                handling_server_requests = False
            except ConnectionAbortedError:
                print(f"Connection to the server was aborted")
                handling_server_requests = False
            except TimeoutError as error:
                print(f"Connection timed out: {error}")
                handling_server_requests = False
            except ConnectionError as error:
                print(f"Connection error occurred: {error}")
                handling_server_requests = False
            except Exception as error:
                print(f"An unexpected error occurred: {error}")
                handling_server_requests = False
