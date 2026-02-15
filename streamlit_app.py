import os
import re
import streamlit as st
from mistralai import Mistral

st.set_page_config(page_title="BankAssist", layout="centered")

APP_TITLE = "BankAssist"
APP_TAGLINE = "Secure, banking-only support (demo)"


API_KEY = os.getenv("MISTRAL_API_KEY")

if not API_KEY:
    st.error("Missing MISTRAL_API_KEY environment variable.")
    st.stop()

client = Mistral(api_key=API_KEY)

MODEL = "mistral-small-latest"  # or whatever your lab requires

SYSTEM_PROMPT = """
You are BankAssist, a banking customer service chatbot.

GOALS:
- Help with banking questions: accounts, cards, transfers, payments, loans, branch info, app login issues.
- Be friendly, professional, and concise.
- Ask a clarifying question if the request is ambiguous.
- If the user asks non-banking questions, politely redirect back to banking.

IMPORTANT SAFETY/ACCURACY:
- Do NOT invent policies, fees, interest rates, APRs, or bank-specific rules.
- If the user requests account-specific actions (balance, transactions, password change), say you cannot access accounts
  and provide general steps instead.
- Never request sensitive info like full card number, PIN, OTP, or passwords.
OUTPUT:
- Plain text only. No markdown headings, no bold, no subject lines.
"""


BANKING_KEYWORDS = [
    "account", "bank", "transfer", "transaction", "card", "debit", "credit",
    "loan", "mortgage", "apr", "interest", "balance", "statement", "iban",
    "swift", "branch", "atm", "fee", "payment", "refund", "charge", "login",
    "password", "otp", "pin"
]

def is_banking_query(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in BANKING_KEYWORDS)

def off_topic_reply():
    return (
        "I’m designed to help with banking questions (accounts, cards, transfers, loans, and app support). "
        "If you have a banking question, tell me what you’re trying to do and I’ll guide you step-by-step."
    )


st.title(APP_TITLE)
st.caption(APP_TAGLINE)

with st.sidebar:
    st.subheader("Quick Actions")
    quick = st.radio(
        "Choose a topic",
        [
            "Open a new account",
            "Card lost or stolen",
            "Transfer not received",
            "Reset / login help",
            "Loan / mortgage info",
            "Branch / ATM info",
        ],
        index=0
    )

    st.divider()
    st.subheader("Escalation")
    st.write("For account-specific help, contact your bank’s official support or visit a branch.")

# Pre-fill helper text based on quick action
quick_prompts = {
    "Open a new account": "I want to open a bank account. What documents do I need and what are the steps?",
    "Card lost or stolen": "My card is lost. What should I do immediately and what happens next?",
    "Transfer not received": "I sent a transfer but it’s not received. What could be wrong and what should I check?",
    "Reset / login help": "I can’t log in to the banking app. How can I reset access safely?",
    "Loan / mortgage info": "Can you explain how fixed-rate vs variable-rate loans differ and what I should consider?",
    "Branch / ATM info": "How do I find my nearest branch/ATM and what are typical banking hours?",
}

st.info("Tip: This bot answers banking questions only (lab demo). It won’t answer unrelated topics.")


if "messages" not in st.session_state:
    st.session_state.messages = []

# Show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Optional button to insert quick prompt
if st.button("Use Quick Action Prompt"):
    user_text = quick_prompts[quick]
else:
    user_text = st.chat_input("Ask a banking question...")


if user_text:
    # display user message
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.write(user_text)

    if not is_banking_query(user_text):
        assistant_text = off_topic_reply()
    else:
        # Build model messages
        model_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        # Include short history (keeps it stable)
        for m in st.session_state.messages[-10:]:
            model_messages.append({"role": m["role"], "content": m["content"]})

        resp = client.chat.complete(
            model=MODEL,
            messages=model_messages,
            temperature=0.3
        )
        assistant_text = resp.choices[0].message.content.strip()

    st.session_state.messages.append({"role": "assistant", "content": assistant_text})
    with st.chat_message("assistant"):
        st.write(assistant_text)
