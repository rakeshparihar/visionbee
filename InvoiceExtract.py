import json
from dotenv import load_dotenv
import streamlit as st
import os
from urllib.parse import urlparse
import requests
import io
from io import BytesIO  # Import BytesIO from the io module
from PIL import Image
import tempfile
import base64 
import streamlit as st
from openai import OpenAI


def load_json_schema(schema_file: str) -> dict:
    with open(schema_file, 'r') as file:
        return json.load(file)

def setup_openai_client():
    api_key = st.secrets['OPENAI_API_KEY']
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)

def base64_to_image(base64_string, output_path):
    # Decode the base64 string to bytes
    image_data = base64.b64decode(base64_string)
    # Use BytesIO to convert this byte data to a binary stream
    image = Image.open(BytesIO(image_data))
    # Save the image to the specified output path
    image.save(output_path, 'PNG')
    return image

def image_to_base64(image):
    # Create a BytesIO buffer to save image
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")  # Save image to buffer in PNG format
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')  # Encode image buffer to Base64
    return img_str


# def fetch_data_and_generate_json(client, image_url, invoice_schema):
#     response = client.chat.completions.create(
#         model='gpt-4o',
#         response_format={"type": "json_object"},
#         messages=[
#             {
#                 "role": "user",
#                 "content": [
#                     {"type": "text", "text": "Provide JSON file that represents this document. Use this JSON Schema: " + json.dumps(invoice_schema)},
#                     {"type": "image_url", "image_url": {"url": image_url}}
#                 ],
#             }
#         ],
#         max_tokens=500,
#     )
#     return response.choices[0].message.content

# def fetch_data_and_generate_json(client, image, invoice_schema):
#     with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
#         image.save(tmp.name)
#         image_url = "file://" + tmp.name
#         response = client.chat.completions.create(
#             model='gpt-4o',
#             response_format={"type": "json_object"},
#             messages=[
#                 {
#                     "role": "user",
#                     "content": [
#                         {"type": "text", "text": "Provide JSON file that represents this document. Use this JSON Schema: " + json.dumps(invoice_schema)},
#                         {"type": "image_url", "image_url": {"url": image_url}}
#                     ],
#                 }
#             ],
#             max_tokens=500,
#         )
#         os.unlink(tmp.name)  # Clean up the temporary file
#     return response.choices[0].message.content


def fetch_data_and_generate_json(client, image, invoice_schema):
    base64_image = image_to_base64(image)
    decoded_image = base64_to_image(base64_image, 'test/test1.png')

    response = client.chat.completions.create(
        model='gpt-4o',
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Provide JSON file that represents this document. Use this JSON Schema: " + json.dumps(invoice_schema)},
                    {"type": "text", "data": base64_image}  # Assuming the API accepts a base64-encoded image
                ],
            }
        ],
        max_tokens=500,
    )
    return response.choices[0].message.content


def repair_json(json_data):
    """Attempt to repair common JSON formatting issues."""
    try:
        # Try adding a closing bracket if it seems the JSON was cut off
        if not json_data.strip().endswith('}'):
            json_data += '}'
        # Attempt to close any open strings or objects
        json_data = json_data.rstrip(",")  # Remove any trailing commas that might cause issues
        return json_data
    except Exception as e:
        print(f"Error during JSON repair: {e}")
        return json_data  # Return the original data if repair fails


def parse_json_data(json_data):
    try:
        return json.loads(json_data)
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
        print("Attempting to fix JSON...")
        repaired_json = repair_json(json_data)
        try:
            return json.loads(repaired_json)
        except json.JSONDecodeError as e:
            print("Failed to repair JSON:", e)
            print("Raw JSON output:", repaired_json)  # Log the attempted repair output
            return {}  # Return an empty dictionary if parsing still fails


def check_image_quality_direct(image):
    return True
    width, height = image.size
    if width < 800 or height < 600:
        return False, "Image resolution is too low."
    return True, "Resolution is sufficient."

# def extractImageFeatures(imageurl):
#     client = setup_openai_client()
#     image_url = imageurl
#     quality_ok, message = check_image_quality(image_url)
#     if not quality_ok:
#         print(message)
#         return
    
#     invoice_schema = load_json_schema('invoice_schema.json')
#     json_response = fetch_data_and_generate_json(client, image_url, invoice_schema)
    
#     json_data = parse_json_data(json_response)
    
#     filename_without_extension = os.path.splitext(os.path.basename(urlparse(image_url).path))[0]
#     json_filename = f"{filename_without_extension}.json"
#     with open(json_filename, 'w') as file:
#         json.dump(json_data, file, indent=4)
    
#     print(f"JSON data saved to {json_filename}")

def handle_image_or_url(client, input_data, invoice_schema, is_url=False):
    if is_url:
        print("image url ", input_data)
        # Handle the image URL directly
        response = client.chat.completions.create(
            model='gpt-4o',
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Provide JSON file that represents this document. Use this JSON Schema: " + json.dumps(invoice_schema)},
                        {"type": "image_url", "image_url": {"url": input_data}}
                    ]
                }
            ],
            max_tokens=500,
        )
    else:
        # Handle the image object
        base64_image = image_to_base64(input_data)
        response = client.chat.completions.create(
            model='gpt-4o',
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Provide JSON file that represents this document. Use this JSON Schema: " + json.dumps(invoice_schema)},
                        {"type": "image_url", "image_url": "data:image/png;base64," + base64_image}  # Base64 needs to be prefixed appropriately
                    ]
                }
            ],
            max_tokens=500,
        )
    return response.choices[0].message.content

