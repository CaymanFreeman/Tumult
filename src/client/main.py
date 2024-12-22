import sys

from PyQt6.QtWidgets import QApplication

from src.client.window import ClientWindow


def main():
    app = QApplication(sys.argv)
    window = ClientWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
