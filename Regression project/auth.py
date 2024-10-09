import streamlit as st
st.set_page_config(page_title = "PriceMyRide", page_icon = "🏎️")
from datetime import datetime 
import firebase_admin
from firebase_admin import credentials, auth, db, storage
import importlib.util
import requests
import os
from PIL import Image
from dotenv import load_dotenv
load_dotenv()

FIREBASE_API_KEY = os.getenv("apiKey")
FIREBASE_AUTH_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
DATABASE_URL = os.getenv("database_url")
STORAGE_BUCKET = os.getenv("storage")

def authenticate_user(email, password):
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(FIREBASE_AUTH_URL, json=payload)
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
    else:
        return {"error": "User profile not found"}

cred = credentials.Certificate("json_key.json")  
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'databaseURL': DATABASE_URL,
        'storageBucket': STORAGE_BUCKET
    })

website_name = "PriceMyRide"
icon_url = "https://t3.ftcdn.net/jpg/01/71/13/24/360_F_171132449_uK0OO5XHrjjaqx5JUbJOIoCC3GZP84Mt.jpg"

st.markdown(
    """
    <style>
        .title-icon-container {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            padding: 10px 0;
        }
        .title-icon-container .icon {
            width: 50px;
            margin-right: 10px;
        }
        .title-icon-container .title {
            font-size: 40px;
            font-weight: bold;
            color: #00BFFF;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 12px;
        }
        .stButton>button:hover {
            background-color: #32CD32;
        }
    </style>
    """, unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="title-icon-container">
        <img class="icon" src="{icon_url}" alt="Car Icon">
        <div class="title">{website_name}</div>
    </div>
    """,
    unsafe_allow_html=True
)

def upload_car_info():
    car_image = st.file_uploader("Upload Car Image", type=['jpg', 'jpeg', 'png'])
    image = None
    
    if car_image is not None:
        image = Image.open(car_image)
        st.image(image, caption='Uploaded Image.', use_column_width=True)

    description = st.text_area("Enter a description about your car")
    user_handle = st.session_state.get('handle', 'Unknown User')

    if st.button("Upload"):
        if car_image is not None and description:
            try:
                bucket = storage.bucket(STORAGE_BUCKET)
                car_image.seek(0)  
                image_file_name = f"car_images/{car_image.name}"
                blob = bucket.blob(image_file_name)

                blob.upload_from_file(car_image)
                blob.make_public()  #
                
                car_info_ref = db.reference("car_info")
                car_info_ref.push({
                    'image_url': blob.public_url,
                    'description': description,
                    'user_handle' : user_handle
                })
                st.success("Car information uploaded successfully!")
            except Exception as e:
                st.error(f"An error occurred while uploading: {e}")
        else:
            st.error("Please upload an image and enter a description.")

def login_page():
    with st.expander("Help", expanded=False):
        st.write(""" 
        **Instructions:**
        - If you do not have an account please SignUp. Please use a valid email.
        - Ensure that the password is at least 6 characters long while creating an account.
        - One should use digits or special symbols as well to make the password strong.
        - You can always change the theme/mode according to your preference from top right.
        """)
        
    choice = st.selectbox('Login/SignUp', ['Login', 'SignUp'])
    email = st.text_input('Please enter your email address')
    password = st.text_input('Please enter your password', type='password')
    
    if choice == 'SignUp':
        confirm_pass = st.text_input('Please confirm your password', type='password')
        handle = st.text_input('Please input your Username', value='Default')
        
        if st.button('Create Account'):
            if password != confirm_pass:
                st.error('Passwords do not match. Please try again.')
            else:
                all_users_ref = db.reference('users')
                all_users = all_users_ref.get()
                
                if all_users:
                    existing_handles = [user_data['handle'] for user_data in all_users.values() if 'handle' in user_data]
                    if handle in existing_handles:
                        st.error(f"The handle '{handle}' is already taken. Please choose another one.")
                        return
                try:
                    user = auth.create_user(email=email, password=password)
                    st.success('Account created successfully.')
                    
                    user_ref = db.reference('users').child(user.uid)
                    user_ref.set({
                        'handle': handle,
                        'email': email,
                        'created_at': datetime.now().isoformat()
                    })
                    st.session_state['handle'] = handle
                    st.session_state['logged_in'] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"An error occurred: {e}")

    elif choice == 'Login':
        if st.button('Login'):
            response = authenticate_user(email, password)
            if "error" in response:
                error_message = response["error"].get("message", "Login failed")
                st.error(f"Error logging in: {error_message}")
            else:
                st.success('Logged in successfully.')
                st.session_state['logged_in'] = True
                st.session_state['handle'] = response.get('handle', 'User')
                st.rerun()

    st.write("""
    ---
    *© 2024 PriceMyRide. The most accurate car price predictor. All rights reserved.*
    """)

def main_website():
    main_website_path = 'website.py' 
    spec = importlib.util.spec_from_file_location("main_website", main_website_path)
    main_website_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_website_module)
    with st.expander("You can upload your car info here that you want to sell...", expanded = False):
        upload_car_info()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    main_website()
    if st.sidebar.button('Logout', key='logout', help='Click to logout'):
        st.session_state['logged_in'] = False
        st.session_state.pop('handle', None) 
        st.success("You've been logged out.")
        st.rerun()
else:
    login_page()
