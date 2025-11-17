import streamlit as st
import pandas as pd
import plotly.express as px
import firebase_admin
from datetime import datetime
import os
from firebase_admin import credentials, db, storage
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.metrics import r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import make_column_transformer
from sklearn.ensemble import RandomForestRegressor
from PIL import Image
import numpy as np


load_dotenv()
DATABASE_URL = os.getenv("database_url")
STORAGE_BUCKET = os.getenv("storage")
cred = credentials.Certificate("json_key.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(
        cred, {"databaseURL": DATABASE_URL, "storageBucket": STORAGE_BUCKET}
    )


website_name = "PriceMyRide"
icon_url = "https://t3.ftcdn.net/jpg/01/71/13/24/360_F_171132449_uK0OO5XHrjjaqx5JUbJOIoCC3GZP84Mt.jpg"

st.markdown(
    f"""
    <div class="title-icon-container">
        <img class="icon" src="{icon_url}" alt="Car Icon">
        <div class="title">{website_name}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


def upload_car_info():
    car_image = st.file_uploader("Upload Car Image", type=["jpg", "jpeg", "png"])
    image = None
    if car_image is not None:
        image = Image.open(car_image)
        st.image(image, caption="Uploaded Image", use_container_width=True)

    description = st.text_area("Enter a short description about your car")
    user_handle = st.session_state.get("handle", "Anonymous User")

    if st.button("Upload"):
        if car_image is not None and description:
            try:
                bucket = storage.bucket(STORAGE_BUCKET)
                car_image.seek(0)
                image_file_name = f"car_info/{car_image.name}"
                blob = bucket.blob(image_file_name)
                blob.upload_from_file(car_image)
                blob.make_public()

                car_info_ref = db.reference("car_info")
                car_info_ref.push(
                    {
                        "image_url": blob.public_url,
                        "description": description,
                        "user_handle": user_handle,
                        "uploaded_on": datetime.now().isoformat(),
                    }
                )
                st.success("Car information uploaded successfully!")
            except Exception as e:
                st.error(f"Upload failed: {e}")
        else:
            st.warning("Please upload an image and enter a description.")


def show_community_page():
    st.markdown("### Community Showcase")
    st.write("See what fellow car enthusiasts are sharing!")

    try:
        car_info_ref = db.reference("car_info")
        car_data = car_info_ref.get()

        if car_data:
            car_data_sorted = sorted(
                car_data.items(),
                key=lambda x: x[1].get("uploaded_on", ""),
                reverse=True,
            )

            for _, car_info in car_data_sorted:
                image_url = car_info.get("image_url")
                description = car_info.get("description", "No description provided.")
                handle = car_info.get("user_handle")
                uploaded_at = car_info.get("uploaded_on", "Unknown date")

                if image_url:
                    st.subheader(f"{handle} uploaded:")
                    st.image(image_url, caption=description, use_container_width=True)
                    st.caption(f"Uploaded on: {uploaded_at}")
                st.markdown("---")
        else:
            st.info("No uploads yet! Be the first to share your car.")
    except Exception as e:
        st.error(f"Error loading community data: {e}")


car = pd.read_csv("Clean_car.csv")
car = car.loc[:, ~car.columns.str.contains("^Unnamed")]
X = car.drop(columns="Price")
y = car["Price"]


def format_indian_number(number):
    if number >= 10000000:
        return f"{number / 10000000:.2f} Cr"
    elif number >= 100000:
        return f"{number / 100000:.2f} Lakh"
    elif number >= 1000:
        return f"{number / 1000:.2f} Thousand"
    else:
        return f"{number:.2f}"


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Josefin+Sans:wght@300;700&family=Lora:wght@400;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Roboto', sans-serif;
        margin: 0;
        padding: 0;
        height: 100%;
        width: 100%;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.8);
        color: white;
    }

    /* Responsive Background */
    .stApp {
        position: relative;
        min-height: 100vh;
        min-width: 100%;
        background-image: url("https://images.unsplash.com/photo-1681245027457-70100eac35e2?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-position: center center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: stretch;
        color: #ffffff;
        overflow-x: hidden;
        z-index: 0;
    }

    /* Dark overlay for readability */
    .stApp::before {
        content: "";
        position: absolute;
        inset: 0;
        background: rgba(0, 0, 0, 0.65);
        z-index: -1;
    }

    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        .stApp {
            background-attachment: scroll;
            background-size: cover;
            background-position: center top;
        }

        [data-testid="stSidebar"] {
            font-size: 14px;
        }

        .title-icon-container .title {
            font-size: 22px;
        }
    }

    /* Title Styling */
    .stTitle, .title {
        color: #FFD700;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.6);
    }

    .title-icon-container {
        display: flex;
        align-items: center;
    }

    .title-icon-container .icon {
        height: 50px;
        margin-right: 15px;
    }

    .title-icon-container .title {
        font-size: 40px;
        font-family: 'Josefin Sans', sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.sidebar.subheader(f"Welcome {st.session_state.get('handle', 'User')}!")
page = st.sidebar.selectbox(
    "Navigate to:", ["Home", "Predictions", "Explore Models", "Community", "About"]
)


if page == "Home":
    st.markdown("## Welcome to PriceMyRide!")
    st.write(
        """
        Buying or selling a car can be tricky — and pricing it right is even trickier!  
        **PriceMyRide** helps you estimate your car’s current market value based on real-world data, 
        brand, fuel type, transmission, and other key details.
        """
    )

    st.markdown(
        """
        ### Why Use PriceMyRide?
        - **Get Accurate Predictions:** Trained on thousands of real-world listings.  
        - **Compare Brands & Models:** Instantly visualize price trends.  
        - **Data-Driven Insights:** Understand what affects car prices the most.  
        - **AI-Powered:** Built using advanced Machine Learning models.  
        - **Cloud-Powered:** Upload and share car info with the community.  
        """
    )

    st.markdown(
        """
        ---
        ### Want to Sell Your Car?
        You can share details and photos of your car below.  
        Other users can view them in the **Community** section.
        """
    )

    with st.expander("Upload Car Info", expanded=False):
        upload_car_info()


elif page == "Predictions":
    st.header("Car Price Prediction")
    st.write(
        "Fill in your car details below and let our model estimate its current value!"
    )

    col1, col2 = st.columns(2)
    with col1:
        selected_brand = st.selectbox("Select Brand", car["Brand"].unique())
        model_df = car[car["Brand"] == selected_brand]
        selected_model = st.selectbox("Select Model", model_df["Model"].unique())
    with col2:
        year_built = st.number_input(
            "Year Built", min_value=2000, max_value=2024, value=2015
        )
        selected_fuel = st.selectbox("Fuel Type", model_df["fuel"].unique())

    col3, col4 = st.columns(2)
    with col3:
        distance_driven = st.number_input("Distance Driven (km)", min_value=0, step=500)
    with col4:
        seller_type = st.selectbox("Seller Type", car["seller_type"].unique())

    col5, col6 = st.columns(2)
    with col5:
        transmission = st.selectbox("Transmission", model_df["transmission"].unique())
    with col6:
        prev_owners = st.selectbox("Previous Owners", ["Zero", "One", "Two"])

    input_data = pd.DataFrame(
        [
            [
                selected_fuel,
                seller_type,
                transmission,
                prev_owners,
                selected_brand,
                selected_model,
                year_built,
                distance_driven,
            ]
        ],
        columns=[
            "fuel",
            "seller_type",
            "transmission",
            "previous_owners",
            "Brand",
            "Model",
            "year_built",
            "km_driven",
        ],
    )

    if st.button("Predict Price"):
        with st.spinner("Calculating..."):
            try:
                ohe = OneHotEncoder(handle_unknown="ignore")
                column_trans = make_column_transformer(
                    (
                        ohe,
                        [
                            "fuel",
                            "seller_type",
                            "transmission",
                            "Brand",
                            "Model",
                            "previous_owners",
                        ],
                    ),
                    remainder="passthrough",
                )
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
                rf = RandomForestRegressor(random_state=42)
                pipe = make_pipeline(column_trans, rf)
                pipe.fit(X_train, y_train)
                pred = pipe.predict(input_data)
                st.balloons()
                st.success(f"Estimated Value: Rs {format_indian_number(pred[0])}")
            except Exception as e:
                st.error(f"Prediction failed: {e}")


elif page == "Explore Models":
    st.header("Explore Car Models")
    selected_brands = st.multiselect("Select Brands", car["Brand"].unique())
    if selected_brands:
        filtered_models = car[car["Brand"].isin(selected_brands)]["Model"].unique()
        selected_models = st.multiselect("Select Models", filtered_models)
        if selected_models:
            filtered_data = car[
                (car["Brand"].isin(selected_brands))
                & (car["Model"].isin(selected_models))
            ]
            comparison_table = (
                filtered_data.groupby(["Brand", "Model"])
                .agg(
                    avg_price=("Price", "mean"),
                    min_price=("Price", "min"),
                    max_price=("Price", "max"),
                )
                .reset_index()
            )
            st.dataframe(comparison_table)
            fig = px.bar(
                filtered_data,
                x="year_built",
                y="Price",
                color="Model",
                title="Price Trends Over the Years",
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select a brand to explore.")


elif page == "Community":
    show_community_page()
    with st.expander("Upload Your Car"):
        upload_car_info()


elif page == "About":
    st.header("About PriceMyRide")
    st.write(
        """
        **PriceMyRide** uses advanced **machine learning models** to predict the resale value of cars.  
        Our data comes from verified automotive listings to ensure accuracy and reliability.
        
        **Tech Stack Used:**
        - Machine Learning: Random Forest Regressor and GridSearch CV 
        - Visualization: Plotly Express  
        - Backend: Firebase Realtime Database & Storage  
        - Frontend: Streamlit  
        """
    )
    st.markdown("---")
    st.caption("© 2024 PriceMyRide. All rights reserved.")

