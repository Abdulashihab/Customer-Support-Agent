from src.agent.agent import chat_turn
from src.tools.account import get_account


def main():
    # "Login": in the real app the website does this. Here we simply ask for the ID.
    subscriber_id = input("Login - enter your 6 digit subscriber ID: ").strip()
    account = get_account(subscriber_id)
    if account is None:
        print("Unknown subscriber ID.")
        return

    print(f"Hello {account['name']}! Type your message, or 'quit' to stop.")
    history = []
    while True:
        message = input("\nYou: ").strip()
        if message.lower() in ("quit", "exit"):
            break
        if not message:
            continue
        try:
            reply = chat_turn(subscriber_id, history, message)
        except Exception as error:
            print("\nSomething went wrong:", error)
            continue
        print("\nAssistant:", reply)


if __name__ == "__main__":
    main()