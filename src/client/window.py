import re
from pathlib import Path
from typing import Optional

from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QMainWindow,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QStackedWidget,
    QWidget,
    QLabel,
)

from src.client.client import Client
from src.protocol import TumultProtocol


class ClientWindow(QMainWindow):

    # IPv4 Regex from Danail Gabenski
    # https://stackoverflow.com/questions/5284147/validating-ipv4-addresses-with-regexp
    IPV4_PATTERN: str = r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$"
    PORT_PATTERN: str = (
        r"^([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$"
    )

    UI_PATH: str = str(Path("assets").joinpath("client.ui"))
    ICON_PATH: str = str(Path("assets").joinpath("icon.png"))

    @classmethod
    def validate_socket_address(cls, address: str, port: int) -> bool:
        if not bool(re.match(cls.IPV4_PATTERN, address)):
            return False
        if not bool(re.match(cls.PORT_PATTERN, str(port))):
            return False

        return True

    def __init__(self):
        super(ClientWindow, self).__init__()
        self.client = Client()

        self.setWindowIcon(QIcon(self.ICON_PATH))
        uic.loadUi(self.UI_PATH, self)

        self.connect_page: Optional[QWidget] = None
        self.chat_page: Optional[QWidget] = None
        self.connect_page_index: Optional[int] = None
        self.chat_page_index: Optional[int] = None
        self.central_stack: Optional[QStackedWidget] = None
        self.form_container: Optional[QWidget] = None
        self.nickname_input: Optional[QLineEdit] = None
        self.server_address_input: Optional[QLineEdit] = None
        self.server_port_input: Optional[QLineEdit] = None
        self.connect_button: Optional[QPushButton] = None
        self.message_box_input: Optional[QLineEdit] = None
        self.send_button: Optional[QPushButton] = None
        self.leave_button: Optional[QPushButton] = None
        self.chat_box: Optional[QTextBrowser] = None
        self.server_name_label: Optional[QLabel] = None
        self.define_widgets()
        self.define_page_indices()

        self.central_stack.setCurrentIndex(self.connect_page_index)
        self.message_box_input.setMaxLength(
            TumultProtocol.max_encoded_chars
            - ((self.nickname_input.maxLength() * 4) + 2)
        )

        self.connect_callbacks()

        self.show()

    def define_page_indices(self):
        self.connect_page_index = self.central_stack.indexOf(self.connect_page)
        self.chat_page_index = self.central_stack.indexOf(self.chat_page)

    def define_widgets(self):
        self.form_container = self.findChild(QWidget, "form_container")
        self.connect_page = self.findChild(QWidget, "connect_page")
        self.chat_page = self.findChild(QWidget, "chat_page")
        self.central_stack = self.findChild(QStackedWidget, "central_stack")
        self.nickname_input = self.findChild(QLineEdit, "nickname_input")
        self.server_address_input = self.findChild(QLineEdit, "server_address_input")
        self.server_port_input = self.findChild(QLineEdit, "server_port_input")
        self.connect_button = self.findChild(QPushButton, "connect_button")
        self.message_box_input = self.findChild(QLineEdit, "message_box_input")
        self.send_button = self.findChild(QPushButton, "send_button")
        self.leave_button = self.findChild(QPushButton, "leave_button")
        self.chat_box = self.findChild(QTextBrowser, "chat_box")
        self.server_name_label = self.findChild(QLabel, "server_name_label")

    def closeEvent(self, event):
        self.client.close_socket()

    def connect_callbacks(self):
        self.connect_button.clicked.connect(self.on_connect_button_clicked)
        self.send_button.clicked.connect(self.on_send_message)
        self.message_box_input.returnPressed.connect(self.on_send_message)
        self.leave_button.clicked.connect(self.on_leave_button_clicked)
        self.central_stack.currentChanged.connect(self.adjustSize)
        self.client.message_received.connect(self.on_message_received)

    def on_connect_button_clicked(self):
        if self.client.server_socket_address:
            return

        entered_server_address = bool(self.server_address_input.text())
        entered_server_port = bool(self.server_address_input.text())

        server_address = (
            self.server_address_input.text()
            if entered_server_address
            else self.client.client_host_address()
        )
        server_port = (
            int(self.server_address_input.text())
            if entered_server_port
            else TumultProtocol.default_port
        )

        if self.validate_socket_address(server_address, server_port):
            self.client.server_socket_address = server_address, server_port
            connection_success = self.client.connect()
            if connection_success:
                self.server_name_label.setText(f"{server_address}:{server_port}")
                entered_nickname = bool(self.nickname_input.text())
                if entered_nickname:
                    self.client.send_nickname(self.nickname_input.text())

                self.central_stack.setCurrentIndex(self.chat_page_index)

    def on_leave_button_clicked(self):
        self.central_stack.setCurrentIndex(self.connect_page_index)
        self.client.close_socket()

    def on_send_message(self):
        message = self.message_box_input.text()
        if message:
            self.client.send_message(message)
        self.message_box_input.clear()

    def on_message_received(self, message: str):
        self.chat_box.append(message)
