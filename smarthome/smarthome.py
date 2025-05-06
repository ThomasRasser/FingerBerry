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

# -------------------------------------------------------- #

# Determine the directory of the script
script_dir = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(script_dir, "config.json")

# Load configuration
with open(config_path) as config_file:
    config = json.load(config_file)

HA_URL = config["HA_URL"]
HA_TOKEN = config["HA_TOKEN"]
ENTITY_ID = config["ENTITY_ID"]

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
    default="toggle",
    show_default=True,
    help="Action to control the smart plug.",
)

# -------------------------------------------------------- #

def main(plug):
    control_smart_plug(plug.lower())

if __name__ == "__main__":
    main()
