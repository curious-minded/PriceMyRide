import streamlit as st
import pandas as pd
import pickle
import plotly.express as px
import firebase_admin
import os
from firebase_admin import credentials, auth, db, storage
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.metrics import r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import make_column_transformer
from sklearn.ensemble import RandomForestRegressor
import numpy as np
from PIL import Image
load_dotenv()

DATABASE_URL = os.getenv("database_url")
STORAGE_BUCKET = os.getenv("storage")
cred = credentials.Certificate("json_key.json")  
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'databaseURL': DATABASE_URL,
        'storageBucket': STORAGE_BUCKET
    })

website_name = "PriceMyRide"
icon_url = "https://t3.ftcdn.net/jpg/01/71/13/24/360_F_171132449_uK0OO5XHrjjaqx5JUbJOIoCC3GZP84Mt.jpg"

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
                blob.make_public()  
                
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

def show_community_page():
    st.write("Check out what the other users are doing!")
    try:
        car_info_ref = db.reference("car_info")
        car_data = car_info_ref.get()
        if car_data:
            for car_id, car_info in car_data.items():
                image_url = car_info.get('image_url')
                description = car_info.get('description', 'No description provided.')
                handle = car_info.get('user_handle')
                if image_url:
                    st.subheader(f"Posted by {handle}:")
                    st.image(image_url, caption=description, use_column_width=True)
                else:
                    st.write("No image available")
                st.markdown("---")  
        else:
            st.write("No user has uploaded anything.")
    except Exception as e:
        st.error(f"An error occurred while fetching community data: {e}")

car = pd.read_csv("Clean_car.csv")
car = car.loc[:, ~car.columns.str.contains('^Unnamed')]
X = car.drop(columns='Price')
y = car['Price']
ohe = OneHotEncoder(handle_unknown = 'ignore')
ohe.fit(X[['fuel', 'seller_type', 'transmission', 'Brand', 'Model', 'previous_owners']])
column_trans = make_column_transformer((OneHotEncoder(categories=ohe.categories_, handle_unknown = 'ignore'), ['fuel', 'seller_type', 'transmission', 'Brand', 'Model', 'previous_owners']),
                                           remainder='passthrough')

def format_indian_number(number):
    if number >= 10000000:
        formatted_number = f"{number / 10000000:.2f} Crs"
    elif number >= 100000:
        formatted_number = f"{number / 100000:.2f} Lakhs"
    elif number >= 1000:
        formatted_number = f"{number / 1000:.2f} Thousand"
    else:
        formatted_number = f"{number:.2f}"
    return formatted_number

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Josefin+Sans:ital,wght@0,100..700;1,100..700&family=Lora:ital,wght@0,400..700;1,400..700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Roboto', sans-serif;
    }
    
    [data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.7);  /* Sidebar with semi-transparent black */
        color: white;
    }
    
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1681245027457-70100eac35e2?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
        background-size: cover;
        background-attachment: fixed;
        color: #FFFFFF;
        filter: brightness(105%);
    }
    
    .stApp::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7); /* Semi-transparent dark overlay */
        z-index: -1; /* Ensure the overlay is behind other elements */
    }
    
    .stTitle {
        color: #FFD700;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.6);
    }
    
    </style>
    """, unsafe_allow_html=True
)

st.sidebar.subheader(f"Welcome to your dashboard {st.session_state.get('handle', 'User')}!")
page = st.sidebar.selectbox("Select a page:", ["Home", "Predictions", "Explore Models", "Community", "About"])

if page == "Home":
    st.write("""
    Welcome to the Car Price Prediction app!
    Do you want to buy a car or sell the one you currently own? 
    This tool will help you estimate the price of the car based on its characteristics such as brand, model, fuel type, transmission, year built, etc.
    """)
    st.markdown("""
    ### Key Features:
    - 🏷️ **Predict Car Prices**: Get an estimate based on your car's specifications.
    - 🔍 **Explore Models**: Compare different brands and models.
    - 📊 **Graphical Analysis**: Visualize the trends using graphs.
    """)
    with st.expander("You can upload your car info here that you want to sell...", expanded = False):
        upload_car_info()

elif page == "Predictions":
    st.header("Predictions")
    st.write("Choose the characteristics of your car and get the results here")
    col1, col2 = st.columns(2)

    with col1:
        Brands = car["Brand"].unique()
        selected_brand = st.selectbox('Select a car brand', Brands)
        Brand_models = car[car["Brand"] == selected_brand]
        Models = Brand_models['Model'].unique()
        selected_model = st.selectbox('Select the car model', Models)

    with col2:
        model_df = car[car['Model'] == selected_model]
        min_year = model_df["year_built"].min()
        max_year = model_df["year_built"].max()
        year_built = st.number_input(
        'Select the year the car was manufactured in:', 
        min_value=min_year, 
        max_value=max_year, 
        value=min_year
    )
        Fuel = model_df["fuel"].unique()
        selected_fuel = st.selectbox('Select the fuel type', Fuel)

    col3, col4 = st.columns(2)

    with col3:
        distance_driven = st.number_input('Enter the distance driven by your car (in kms):', min_value=0, value=0, step=500)

    with col4:
        seller = car['seller_type'].unique()
        seller_type = st.selectbox('Select the seller type', seller)

    col5, col6 = st.columns(2)

    with col5:
        trans = model_df['transmission'].unique()
        transmission = st.selectbox('Select the transmission type of the car', trans)

    with col6:
        prev_owners = st.selectbox('Enter number of previous owners:', ['Zero', 'One', 'Two'])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=370)
    rf = RandomForestRegressor(random_state=370)
    pipe = make_pipeline(column_trans, rf)
    pipe.fit(X_train, y_train)

    input_data = pd.DataFrame([[selected_fuel, seller_type, transmission, prev_owners, selected_brand, selected_model, year_built, distance_driven]],
                            columns=['fuel', 'seller_type', 'transmission', 'previous_owners', 'Brand', 'Model', 'year_built', 'km_driven'])
    
    if st.button('Predict the price'):
        st.markdown("""
        <style>
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
        """, unsafe_allow_html=True)
        try:
            pred = pipe.predict(input_data)
            st.balloons()
            st.success(f'The estimated value of the car is: Rs {format_indian_number(pred[0])}')
            st.info("Greatness takes some time to deliver...")
        except ValueError as e:
            st.error(f"Error: {str(e)}") 

    with st.expander("You can upload your car info here that you want to sell...", expanded = False):
        upload_car_info()

elif page == "Explore Models":
    st.write("### Select Car Brands")
    with st.expander("Help", expanded=False):
        st.write("""
        **Instructions:**
        - Use the dropdown to select one or more car brands.
        - After selecting brands, you will be able to choose models associated with these brands.
        - The selected models will be used for comparison.
        """)
    selected_brands = st.multiselect(
        'Select car brands to compare',
        car['Brand'].unique(),
        help="Once you are done selecting, please click outside the drop-down menu."
    )
    if selected_brands:
        filtered_models = car[car['Brand'].isin(selected_brands)]['Model'].unique()
        selected_models = st.multiselect(
            'Select car models to compare',
            filtered_models,
            help="Once you are done selecting, please click outside the drop-down menu."
        )
        if selected_models:
            filtered_data = car[(car['Brand'].isin(selected_brands)) & (car['Model'].isin(selected_models))]
            if not filtered_data.empty:
                st.write("### Comparison Table")
                comparison_table = filtered_data.groupby(['Brand', 'Model']).agg(
                    avg_price=pd.NamedAgg(column='Price', aggfunc='mean'),
                    median_price=pd.NamedAgg(column='Price', aggfunc='median'),
                    min_price=pd.NamedAgg(column='Price', aggfunc='min'),
                    max_price=pd.NamedAgg(column='Price', aggfunc='max'),
                ).reset_index()
                st.dataframe(comparison_table)

                avg_price_per_year = filtered_data.groupby(['year_built', 'Model']).agg(
                avg_price=('Price', 'mean')
            ).reset_index()
                fig2 = px.bar(
                    avg_price_per_year,
                    x='year_built',
                    y='avg_price',
                    color='Model',
                     barmode='group',
                    title='Price Variation of Selected Models Over Years',
                    labels={'avg_price': 'Average Price'}
                )
                st.plotly_chart(fig2, use_container_width=True)

        else:
            st.warning("Please select atleast one car Model.")
    else:
        st.warning("Please select atleast one car Brand.")

    with st.expander("You can upload your car info here that you want to sell...", expanded = False):
        upload_car_info()

elif page == "Community":
    st.header("Community")
    show_community_page()
    with st.expander("You can upload your car info here that you want to sell...", expanded = False):
        upload_car_info()

elif page == "About":
    st.header("About")
    st.write("""
    ### About This Web Service
    - This web service utilizes machine learning to predict the prices of used cars based on various attributes. 
    - It uses the concepts of Random Forests to predict the prices of cars based on the attributes
    provided by the user which can produce highly varying results if changed. 
    - The data was taken from the [Kaggle](https://www.kaggle.com/). 
    - It provides insights into the pricing trends and allows users to explore car models. 
    - Data might not contain various other brands/models or the latest updates in the automobile industry so the predictions may vary.
    - [Streamlit](https://streamlit.io/) and [Firebase](https://firebase.google.com/) were used for front-end and back-end services respectively. 
    - Plotly was used to plot bar graphs and pie charts for data analysis.
    """)

    selected_brands = st.multiselect(
    'Select car brands to get an idea of what the dataset comprises of',
    car['Brand'].unique(),
    help="Once you are done selecting, please click outside the drop-down menu."
)
    if selected_brands:
        for brand in selected_brands:
            brand_data = car[car['Brand'] == brand]
            brand_model_counts = brand_data.groupby('Model').size().reset_index(name='Count')
            brand_model_counts['Percentage'] = (brand_model_counts['Count'] / brand_model_counts['Count'].sum()) * 100
            
            fig = px.pie(
                brand_model_counts,
                names='Model',
                values='Percentage',
                title=f'Percentage of data of each model in {brand}',
                hole=0.3,
                color='Model'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Please select at least one car brand to display the charts.")

st.write("""
    ---
    *© 2024 PriceMyRide. The most accurate car price predictor. All rights reserved.*
    """)
