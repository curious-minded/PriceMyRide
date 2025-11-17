import streamlit as st
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
import importlib.util
import firebase_admin
from firebase_admin import credentials, db

# Load env
load_dotenv()
FIREBASE_API_KEY = os.getenv("apiKey")
DATABASE_URL = os.getenv("database_url")

# Firebase REST endpoints
SIGNUP_URL = (
    f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
)
LOGIN_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
LOOKUP_URL = (
    f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_API_KEY}"
)
SEND_OOB_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"

# Initialize Firebase Admin for Realtime Database
cred = credentials.Certificate("json_key.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})

# UI variables
website_name = "PriceMyRide"
icon_url = "https://t3.ftcdn.net/jpg/01/71/13/24/360_F_171132449_uK0OO5XHrjjaqx5JUbJOIoCC3GZP84Mt.jpg"

st.markdown(
    """
<style>
.title-icon-container { display: flex; align-items: center; padding: 10px 0; }
.title-icon-container .icon { width: 50px; margin-right: 10px; }
.title-icon-container .title { font-size: 40px; font-weight: bold; color: #00BFFF; }
.stButton>button { background-color: #4CAF50; color: white; padding: 10px 20px; border-radius: 12px; }
.stButton>button:hover { background-color: #32CD32; }
</style>
""",
    unsafe_allow_html=True,
)


# Helper functions
def send_verification_email(id_token):
    payload = {"requestType": "VERIFY_EMAIL", "idToken": id_token}
    requests.post(SEND_OOB_URL, json=payload)


def send_password_reset_email(email):
    payload = {"requestType": "PASSWORD_RESET", "email": email}
    requests.post(SEND_OOB_URL, json=payload)


def signup_user(email, password, display_name):
    payload = {
        "email": email,
        "password": password,
        "displayName": display_name,
        "returnSecureToken": True,
    }
    resp = requests.post(SIGNUP_URL, json=payload).json()
    if "error" in resp:
        return {"error": resp["error"]["message"]}

    # Send email verification
    send_verification_email(resp["idToken"])

    # Save profile to Realtime Database
    user_id = resp["localId"]
    db.reference("users").child(user_id).set(
        {
            "handle": display_name,
            "email": email,
            "created_at": datetime.now().isoformat(),
        }
    )
    return {"success": True}


def authenticate_user(email, password):
    payload = {"email": email, "password": password, "returnSecureToken": True}
    resp = requests.post(LOGIN_URL, json=payload).json()
    if "error" in resp:
        return {"error": resp["error"]["message"]}

    # Check email verification
    lookup_resp = requests.post(LOOKUP_URL, json={"idToken": resp["idToken"]}).json()
    user_info = lookup_resp["users"][0]
    if not user_info["emailVerified"]:
        return {"error": "Email not verified. Please check your inbox."}

    return {
        "success": True,
        "handle": user_info.get("displayName", "User"),
        "idToken": resp["idToken"],
    }


# Streamlit login/signup
def login_page():
    st.markdown(
        f"""
    <div class="title-icon-container">
        <img class="icon" src="{icon_url}" alt="Car Icon">
        <div class="title">{website_name}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    with st.expander("Help (New Users)", expanded=False):
        st.write(
            """
        - If you are new, please **SignUp** with a valid email address.
        - After signing up, check your inbox and **verify your email**.
        - Once verified, login using your credentials.
        - You can change the theme from the top-right menu.
        - Use **Forgot Password** if you need to reset your password.
        """
        )

    choice = st.selectbox(
        "Login / SignUp / Forgot Password", ["Login", "SignUp", "Forgot Password"]
    )
    email = st.text_input("Email")
    password = (
        st.text_input("Password", type="password")
        if choice != "Forgot Password"
        else None
    )

    if choice == "SignUp":
        confirm_pass = st.text_input("Confirm Password", type="password")
        handle = st.text_input("Username", value="Default")
        if st.button("Create Account"):
            if password != confirm_pass:
                st.error("Passwords do not match.")
                return
            resp = signup_user(email, password, handle)
            if "error" in resp:
                st.error(f"Error: {resp['error']}")
            else:
                st.success(
                    "Account created. Check your inbox or spam folder for verification email. Once verified, continue with login."
                )

    elif choice == "Login":
        if st.button("Login"):
            resp = authenticate_user(email, password)
            if "error" in resp:
                st.error(resp["error"])
            else:
                st.session_state["logged_in"] = True
                st.session_state["handle"] = resp["handle"]
                st.success(f"Welcome {resp['handle']}!")
                st.rerun()

    elif choice == "Forgot Password":
        if st.button("Send Reset Email"):
            send_password_reset_email(email)
            st.info(
                f"Password reset message has been sent to your registered email. Once your password is reset, continue with login."
            )

    st.write("---")
    st.write("*© 2024 PriceMyRide. All rights reserved.*")


# Main website loader
def main_website():
    main_website_path = "website.py"
    spec = importlib.util.spec_from_file_location("main_website", main_website_path)
    main_website_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_website_module)


# Initialize session
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
    main_website()
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state.pop("handle", None)
        st.success("Logged out successfully.")
        st.rerun()
else:
    login_page()
