import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import json 
from InvoiceExtract import setup_openai_client, fetch_data_and_generate_json, parse_json_data, load_json_schema, handle_image_or_url

icon_path = "cxr.png"

st.set_page_config(
    page_title="Vision Bee: Medical Product Feature Detector",
    page_icon=icon_path
)

def process_input(uploaded_file, image_url=None):
    try:
        client = setup_openai_client()
        invoice_schema = load_json_schema('invoice_schema.json')
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption='Uploaded Image', use_column_width=True)
            json_response = handle_image_or_url(client, image, invoice_schema, is_url=False)
        elif image_url:
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            st.image(image, caption='Uploaded Image', use_column_width=True)
            json_response = handle_image_or_url(client, image_url, invoice_schema, is_url=True)

        json_data = parse_json_data(json_response)
        return json_data
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

st.title("Vision Bee: Medical Product Feature Detector")
image_url = st.text_input("Or enter an Image URL")
uploaded_file = st.file_uploader("Choose an Image", type=['png', 'jpg', 'jpeg'])

if st.button("Process Image"):
    processed_data = process_input(uploaded_file, image_url)
    if processed_data:
        st.success("Features extracted successfully.")
        st.json(processed_data)
        st.download_button("Download Data (JSON)", json.dumps(processed_data), "features.json", "application/json")
    else:
        st.error("Failed to process image.")
