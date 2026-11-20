import sys
from pathlib import Path

# Streamlit runs this file from the ui folder, so we add the project folder
# to Python's search path. Without this, "from src..." would not work.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from src.agent.agent import chat_turn
from src.auth.login import request_otp, verify_otp
from src.tools.account import get_account
from src.tools.work_orders import get_work_orders

st.set_page_config(page_title="Customer Support")

OTP_MESSAGES = {
    "wrong_code": "That code is not correct.",
    "otp_expired": "That code has expired. Please ask for a new one.",
    "too_many_attempts": "Too many wrong tries. Please ask for a new code.",
    "no_otp_requested": "Please ask for a code first.",
}


def start_state():
    """Create the values this page remembers between clicks."""
    defaults = {
        "stage": "phone",        # phone -> otp -> choose -> chat
        "rmn": "",
        "demo_code": "",
        "connections": [],
        "subscriber_id": None,
        "history": [],           # what the AI remembers
        "chat": [],              # what we show on the screen
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def log_out():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def phone_page():
    st.title("Customer Support")
    st.write("Log in with your registered mobile number.")
    rmn = st.text_input("Registered mobile number", max_chars=10)
    if st.button("Send code"):
        result = request_otp(rmn.strip())
        if result["ok"]:
            st.session_state.rmn = rmn.strip()
            st.session_state.demo_code = result["otp"]
            st.session_state.stage = "otp"
            st.rerun()
        else:
            st.error("This mobile number is not registered.")


def otp_page():
    st.title("Enter your code")
    # DEMO ONLY: a real app would send the code by SMS instead of showing it.
    st.info(f"Demo only: your code is {st.session_state.demo_code}")
    code = st.text_input("6 digit code", max_chars=6)
    if st.button("Log in"):
        result = verify_otp(st.session_state.rmn, code)
        if result["ok"]:
            st.session_state.connections = result["connections"]
            if len(result["connections"]) == 1:
                st.session_state.subscriber_id = result["connections"][0]["subscriber_id"]
                st.session_state.stage = "chat"
            else:
                st.session_state.stage = "choose"
            st.rerun()
        else:
            st.error(OTP_MESSAGES.get(result["reason"], "Something went wrong."))
            if result["reason"] != "wrong_code":
                st.session_state.stage = "phone"


def choose_page():
    st.title("Choose your connection")
    options = {
        f"{c['subscriber_id']} ({c['kind']})": c["subscriber_id"]
        for c in st.session_state.connections
    }
    label = st.radio("Which connection do you need help with?", list(options))
    if st.button("Continue"):
        st.session_state.subscriber_id = options[label]
        st.session_state.stage = "chat"
        st.rerun()


def chat_page():
    subscriber_id = st.session_state.subscriber_id
    account = get_account(subscriber_id)

    with st.sidebar:
        st.header(account["name"])
        st.write(f"Subscriber ID: {subscriber_id} ({account['kind']})")
        st.write(f"Status: {account['status']}")
        st.write(f"Balance: Rs. {account['balance']:.0f}")
        st.write(f"Monthly charge: Rs. {account['monthly_charge']:.0f}")
        st.write(f"Due date: {account['due_date']}")
        st.write("Packs: " + ", ".join(p["pack_id"] for p in account["packs"]))
        orders = get_work_orders(subscriber_id)
        if orders:
            st.write("Work orders:")
            for order in orders:
                st.write(f"- {order['wo_id']}: {order['issue_type']} ({order['status']})")
        if st.button("Log out"):
            log_out()

    st.title("Customer Support")
    for item in st.session_state.chat:
        with st.chat_message(item["role"]):
            st.write(item["content"])

    prompt = st.chat_input("Type your message")
    if prompt:
        st.session_state.chat.append({"role": "user", "content": prompt})
        try:
            with st.spinner("Thinking..."):
                reply = chat_turn(subscriber_id, st.session_state.history, prompt)
        except Exception as error:
            reply = f"Sorry, something went wrong: {error}"
        st.session_state.chat.append({"role": "assistant", "content": reply})
        st.rerun()   # reload so the sidebar shows any change


start_state()
stage = st.session_state.stage
if stage == "phone":
    phone_page()
elif stage == "otp":
    otp_page()
elif stage == "choose":
    choose_page()
else:
    chat_page()