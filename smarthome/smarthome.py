# Usage
# run the program with option --help, to see usage:
# python3 main.py --help

# -------------------------------------------------------- #

import requests
import json
import subprocess
import click
import time
import os

from dotenv import load_dotenv

# -------------------------------------------------------- #

# Load environment variables from .env file
script_dir = os.path.dirname(os.path.realpath(__file__))
env_path = os.path.join(script_dir, ".env")
load_dotenv(env_path)

HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")
ENTITY_ID = os.getenv("ENTITY_ID")
PB_KEY = os.getenv("PUSHBULLET_API_KEY")
PB_DEVICE_IDEN = os.getenv("PUSHBULLET_DEVICE_IDEN")

# -------------------------------------------------------- #

def send_message(message: str) -> None:
    headers = {
        "Access-Token": PB_KEY,
        "Content-Type": "application/json"
    }
    url = "https://api.pushbullet.com/v2/pushes"
    message_data = {
        "device_iden": PB_DEVICE_IDEN,
        "type": "note",
        "body": message
    }

    try:
        response = requests.post(url, headers=headers, json=message_data, timeout=10)
        if response.status_code == 200:
            print("Message sent successfully to tablet.")
        else:
            print("Failed to send message:", response.status_code, response.text)
    except requests.RequestException as e:
        print("Error during message request:", e)

def control_smartphone_light(action):
    if action == "on":
        send_message("LIGHT ON")
    elif action == "off":
        send_message("LIGHT OFF")
    else:
        print("Invalid toggle action specified.")


# -------------------------------------------------------- #

# Function to send a request to the Home Assistant API
def send_ha_request(service):
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    url = f"{HA_URL}/api/services/switch/{service}"
    data = {"entity_id": ENTITY_ID}

    try:
        response = requests.post(url, headers=headers, json=data, timeout=5)
        if response.status_code == 200:
            print(f"Smart plug {service} successfully.")
        else:
            print(f"Failed to {service} smart plug.", response.status_code, response.text)
    except requests.RequestException as e:
        print(f"Error during {service} request:", e)



# Change the smart plug state
def control_smart_plug(action):
    if action == "on":
        send_ha_request("turn_on")
    elif action == "off":
        send_ha_request("turn_off")
    elif action == "toggle":
        send_ha_request("toggle")
    elif action == "none":
        pass
    else:
        print("Invalid toggle action specified.")

# -------------------------------------------------------- #

@click.command()
@click.option(
    "--plug",
    type=click.Choice(["on", "off", "toggle", "none"], case_sensitive=False),
    default="none",
    show_default=True,
    help="Action to control the smart plug.",
)
@click.option(
    "--phone",
    type=str,
    required=False,
    help="Message to send to the phone via Pushbullet.",
)

# -------------------------------------------------------- #

def main(plug, phone):
    if plug:
        control_smart_plug(plug.lower())

    if phone:
        send_message(phone)

if __name__ == "__main__":
    main()
