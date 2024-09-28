# import streamlit as st
# import firebase_admin
# from firebase_admin import auth, exceptions, credentials, initialize_app
# import asyncio
# from httpx_oauth.clients.google import GoogleOAuth2

# cred = credentials.Certificate("json_project.json")
# try:
#     firebase_admin.get_app()
# except ValueError as e:
#     initialize_app(cred)

# client_id = st.secrets["client_id"]
# client_secret = st.secrets["client_secret"]
# redirect_url = "http://localhost:8501/"  

# client = GoogleOAuth2(client_id=client_id, client_secret=client_secret)


# st.session_state.email = ''

# async def get_access_token(client: GoogleOAuth2, redirect_url: str, code: str):
#     return await client.get_access_token(code, redirect_url)

# async def get_email(client: GoogleOAuth2, token: str):
#     user_id, user_email = await client.get_id_email(token)
#     return user_id, user_email

# def get_logged_in_user_email():
#     try:
#         query_params = st.experimental_get_query_params()
#         code = query_params.get('code')
#         if code:
#             token = asyncio.run(get_access_token(client, redirect_url, code))
#             st.experimental_get_query_params()

#             if token:
#                 user_id, user_email = asyncio.run(get_email(client, token['access_token']))
#                 if user_email:
#                     try:
#                         user = auth.get_user_by_email(user_email)
#                     except exceptions.FirebaseError:
#                         user = auth.create_user(email=user_email)
#                     st.session_state.email = user.email
#                     return user.email
#         return None
#     except:
#         pass


# def show_login_button():
#     authorization_url = asyncio.run(client.get_authorization_url(
#         redirect_url,
#         scope=["email", "profile"],
#         extras_params={"access_type": "offline"},
#     ))
#     st.markdown(f'<a href="{authorization_url}" target="_self">Login</a>', unsafe_allow_html=True)
#     get_logged_in_user_email()

# def app():
#     st.title('Welcome!')
#     if not st.session_state.email:
#         get_logged_in_user_email()
#         show_login_button()

#     if st.session_state.email:
#         st.write(st.session_state.email)
#         if st.button("Logout", type="primary", key="logout_non_required"):
#             st.session_state.email = ''
#             st.rerun()

# app()
import streamlit as st
from firebase_setup import initialize_firebase
from firebase_admin import db
from google.oauth2 import id_token
from google_auth_oauthlib import get_user_credentials
import requests

# Initialize Firebase
initialize_firebase()

st.title(":closed_lock_with_key: Google Authentication with Firebase")

def login_callback():
    credentials = get_user_credentials(
        client_id=st.secrets["client_id"],
        client_secret=st.secrets["client_secret"],
        scopes=[
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            "https://www.googleapis.com/auth/calendar.events.readonly",
        ],
        minimum_port=8501,
        maximum_port=8502,
    )
    st.session_state.credentials = credentials

    # Verify the token and get user info
    id_info = id_token.verify_oauth2_token(
        credentials.id_token,
        requests.Request(),
        st.secrets["client_id"]
    )
    
    # Save user data to Firebase
    user_ref = db.reference(f'users/{id_info["sub"]}')
    user_ref.set({
        'name': id_info['name'],
        'email': id_info['email'],
        'picture': id_info['picture']
    })

    st.write(f"User details added to Firebase: {id_info}")

# Create a login button that triggers the Google login flow
st.button(':key: Login with Google', type='primary', on_click=login_callback)

# Display user info if logged in
if 'credentials' in st.session_state:
    id_info = id_token.verify_oauth2_token(
        st.session_state.credentials.id_token,
        requests.Request(),
        st.secrets["client_id"]
    )
    st.json(id_info)
