from client import Client


def main():
    client = Client()
    client.connect()

    while True:
        user_input = input()
        if user_input == "/dc" or user_input == "/disconnect":
            client.send_disconnect()
            break
        else:
            client.send_message(user_input)


if __name__ == "__main__":
    main()
