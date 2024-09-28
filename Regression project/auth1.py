import streamlit as st
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, auth, db, exceptions, storage
import os
from dotenv import load_dotenv
import requests
import importlib.util
load_dotenv()
st.set_page_config(page_title="GEMINI Assistant", page_icon="🦉")

FIREBASE_API_KEY2 = os.getenv("apiKey2")
FIREBASE_AUTH_URL2 = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY2}"
DATABASE_URL2 = os.getenv("database_url2")

cred = credentials.Certificate("json_project.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL2})

st.markdown("""
    <style>
    .title {
        font-family: 'Helvetica', sans-serif;
        font-size: 48px;
        color: #39FF14;
        text-align: center;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        font-size: 18px;
        border-radius: 10px;
        padding: 10px 20px;
    }
    .stButton > button:hover {
        background-color: #39FF14;
    }
    .logout-button > button {
        background-color: #F08080;
        color: white;
        font-size: 18px;
        border-radius: 10px;
        padding: 10px 20px;
    }
    .logout-button > button:hover {
        background-color: #FF0000;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">Welcome to GEMINI 🦉</div>', unsafe_allow_html=True)

# client_id = st.secrets["client_id"]
# client_secret = st.secrets["client_secret"]
# redirect_url = "http://localhost:8501/"

# client = GoogleOAuth2(client_id=client_id, client_secret=client_secret)

# if 'email' not in st.session_state:
#     st.session_state.email = ''
if 'logged_in' not in st.session_state:
    st.session_state["logged_in"] = False

# async def get_access_token(client: GoogleOAuth2, redirect_url: str, code: str):
#         return await client.get_access_token(code, redirect_url)

# async def get_email(client: GoogleOAuth2, token: str):
#     user_id, user_email = await client.get_id_email(token)
#     return user_id, user_email

# def store_user_data(user_id, email):
#     user_ref = db.reference(f'users/{user_id}')
#     user_ref.set({
#         'email': email,
#         'created_at': datetime.now().isoformat()
#     })

# def get_logged_in_user_email():
#     try:
#         query_params = st.query_params
#         code = query_params.get('code')
#         if code:
#             token = asyncio.run(get_access_token(client, redirect_url, code))
#             st.query_params
#             if token:
#                 user_id, user_email = asyncio.run(get_email(client, token['access_token']))
#                 if user_email:
#                     try:
#                         user = auth.get_user_by_email(user_email)
#                     except exceptions.FirebaseError:
#                         user = auth.create_user(email=user_email)
#                     st.session_state.email = user.email
#                     st.session_state["logged_in"] = True
#                     #st.session_state['handle'] = user.email
#                     store_user_data(user.uid, user.email)
#                     st.query_params
#                     return user.email
#         return None
#     except Exception as e:
#         st.error(f"Failed to get user email: {e}")
#         return None


# def show_login_button():
#     try:
#         authorization_url = asyncio.run(client.get_authorization_url(
#             redirect_url,
#             scope=["email", "profile"],
#             extras_params={"access_type": "offline"},
#         ))
#         st.markdown(f'<a href="{authorization_url}" target="_self">Login with Google</a>', unsafe_allow_html=True)
#         get_logged_in_user_email()
#     except Exception as e:
#         st.error(f"Failed to create authorization URL: {e}")

def authenticate_user(email, password):
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(FIREBASE_AUTH_URL2, json=payload)
    auth_response = response.json()

    if "error" in auth_response:
        return {"error": auth_response["error"]}

    id_token = auth_response.get("idToken")
    local_id = auth_response.get("localId")

    user_ref = db.reference(f'users/{local_id}')
    user_profile = user_ref.get()

    if user_profile:
        return {
            "handle": user_profile.get("handle"),
            "email": user_profile.get("email")
        }
    return {"error": "User profile not found"}

def login_page():
    with st.expander("Help", expanded=False):
        st.write("""
        **Instructions:**
        - If you do not have an account please SignUp.
        - If you are new to this site please ensure the password is at least 6 characters long while creating an account.
        """)

    choice = st.selectbox('Login/SignUp', ['Login', 'SignUp'])

    if choice == 'SignUp':
        email = st.text_input('Please enter your email address')
        password = st.text_input('Please enter your password', type='password')
        confirm_pass = st.text_input('Please confirm your password', type='password')
        handle = st.text_input('Please input your Username', value='Default')
        if st.button('Create Account'):
            if password != confirm_pass:
                st.error('Passwords do not match. Please try again.')
            else:
                user = auth.create_user(email=email, password=password)
                st.success('Account created successfully!')
                user_ref = db.reference('users').child(user.uid)
                user_ref.set({
                    'handle': handle,
                    'email': email,
                    'created_at': datetime.now().isoformat()
                })
                st.session_state['handle'] = handle
                st.title('Welcome ' + handle)
                st.info('Login via the drop-down menu.')

    elif choice == 'Login':
        email = st.text_input('Please enter your email address')
        password = st.text_input('Please enter your password', type='password')
        if st.button('Login'):
            response = authenticate_user(email, password)
            if "error" in response:
                error_message = response["error"].get("message", "Login failed")
                st.error(f"Error logging in: {error_message}")
            else:
                st.success('Logged in successfully!')
                st.session_state['logged_in'] = True
                st.session_state['handle'] = response.get('handle', 'User')
                st.rerun()

    # elif choice == 'Sign in with Google':
    #     if not st.session_state["logged_in"]:
    #         get_logged_in_user_email()
    #         if not st.session_state.email:
    #             show_login_button()

def main_website():
    main_website_path = 'example.py'
    spec = importlib.util.spec_from_file_location("main_website", main_website_path)
    main_website_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_website_module)

if st.session_state['logged_in']:
    main_website()
    if st.sidebar.button('Logout', key='logout', help='Click to log out'):
        st.session_state['logged_in'] = False
        st.session_state.pop('handle', None)
        st.query_params 
        st.rerun()
else:
    login_page()
