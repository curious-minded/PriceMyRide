import streamlit as st
from datetime import datetime 
import firebase_admin
from firebase_admin import credentials, auth, db, storage
import importlib.util
import requests
import os
from dotenv import load_dotenv
load_dotenv()

FIREBASE_API_KEY = st.secrets["apiKey"]
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=" + FIREBASE_API_KEY
DATABASE_URL = st.secrets["database_url"]
STORAGE = st.secrets["storage1"]
firebase_credentials = st.secrets["firebase"]
cred = credentials.Certificate(firebase_credentials)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL,
                                  'storageBucket': STORAGE})

st.markdown("""
    <style>
    .title {
        font-family: 'Helvetica', sans-serif;
        font-size: 48px;
        color: #0000FF;
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

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def authenticate_user(email, password):
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    
    response = requests.post(FIREBASE_AUTH_URL, json=payload)
    auth_response = response.json()
    
    if "error" in auth_response:
        return {"error": auth_response["error"]["message"]}  
    
    id_token = auth_response.get("idToken")
    local_id = auth_response.get("localId")  
    
    user_ref = db.reference(f'users/{local_id}')
    user_profile = user_ref.get()
    
    if user_profile:
        return {
            "handle": user_profile.get("handle"),
            "email": user_profile.get("email"),
            "id_token": id_token 
        }
    else:
        return {"error": "User profile not found"}

def upload_file(file):
    bucket = storage.bucket()
    blob = bucket.blob(file.name)
    blob.upload_from_file(file)
    return blob.public_url

def login_page():
    st.markdown('<div class="title">Welcome to PriceMyRide 🚘</div>', unsafe_allow_html=True)
    with st.expander("Help", expanded=False):
            st.write("""
    **Instructions:**
    - If you do not have an account please SignUp.
    - If you are new to this site please ensure the password is atleast 6 characters long while creating an account.
    """)
    choice = st.selectbox('Login/SignUp', ['Login', 'SignUp'])
    email = st.text_input('Please enter your email address')
    password = st.text_input('Please enter your password', type='password')
    if choice == 'SignUp':
        confirm_pass = st.text_input('Please confirm your password', type='password')
        handle = st.text_input('Please input your Username', value='Default')
        if st.button('Create Account'):
            if password != confirm_pass:
                st.error('Passwords do not match. Please try again')
            else:
                user = auth.create_user(
                        email=email,
                        password=password
                    )
                st.success('Account created successfully')
                user_ref = db.reference('users').child(user.uid)
                user_ref.set({
                        'handle': handle,
                        'email': email,
                        'created_at': datetime.now().isoformat()
                    })
                st.session_state['handle'] = handle
                st.title('Welcome ' + handle)
                st.info('Login via the drop-down menu')

    elif choice == 'Login':
        if st.button('Login'):
           response = authenticate_user(email, password)
           if "error" in response:
            error_message = response["error"]
            st.error(f"Error logging in: {error_message}")
           else:
            st.success('Logged in successfully')
            st.session_state['logged_in'] = True
            st.session_state['handle'] = response.get('handle', 'User')
            st.rerun()


def main_website():
    main_website_path = 'website.py' 
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
        
