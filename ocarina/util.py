import os
import sys

import json

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

def emit(task, payload):
    payload["username"] = config["MAJORA_USERNAME"]
    payload["token"] = config["MAJORA_TOKEN"]

    r = requests.post(config["MAJORA_DOMAIN"] + ENDPOINTS[task] + '/',
            headers = {"Content-Type": "application/json", "charset": "UTF-8"},
            json = payload,
    )
    print (r.json())
    return r.json()
