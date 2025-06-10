import base64
import os
import requests
import logging

def get_camera_image():
    """
    Fetches the image from the specified Home Assistant camera entity.
    """
    camera_entity_id = os.getenv("CAMERA_ENTITY_ID")
    supervisor_token = os.getenv("SUPERVISOR_TOKEN")

    if not camera_entity_id or not supervisor_token:
        logging.error("Error: CAMERA_ENTITY_ID or SUPERVISOR_TOKEN not set.")
        return None

    api_url = f"http://supervisor/core/api/camera_proxy/{camera_entity_id}"
    headers = {"Authorization": f"Bearer {supervisor_token}"}

    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode("utf-8")
        else:
            logging.error(f"Error fetching image: {response.status_code} - {response.text}")
            return None
    except requests.RequestException as e:
        logging.error(f"Error getting camera image: {e}")
        return None