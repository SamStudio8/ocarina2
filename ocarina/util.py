import os
import sys

import json
import requests

from . import client

def get_config():
    config = None
    config_path = os.path.expanduser("~/.ocarina")
    if os.path.exists(config_path):
        with open(config_path) as config_fh:
            config = json.load(config_fh)
            return config
    else:
        sys.stderr.write('''No configuration file found.\nCopy the command from below to initialise,\nthen edit the file and fill in the configration keys.\n''')
        sys.stderr.write('''echo '{"MAJORA_DOMAIN": "https:\\...\", "MAJORA_USER": "", "MAJORA_TOKEN": ""}' > ~/.ocarina''')
        sys.exit(1)

def emit(endpoint, payload):
    config = get_config()
    payload["username"] = config["MAJORA_USER"]
    payload["token"] = config["MAJORA_TOKEN"]
    payload["client_name"] = "ocarina"
    payload["client_version"] = client.CLIENT_VERSION

    r = requests.post(config["MAJORA_DOMAIN"] + endpoint + '/',
            headers = {"Content-Type": "application/json", "charset": "UTF-8"},
            json = payload,
    )
    print (r.json())
    return r.json()
