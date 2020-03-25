import os
import sys

import json

CLIENT_VERSION = "0.0.1"
ENDPOINTS = {
        "api.artifact.biosample.add": "api/v2/artifact/biosample/add/",
        "api.process.sequencing.add": "api/v2/process/sequencing/add/",
}

def emit(base_endpoint, payload, to_uuid=None):
    payload["key"] = conf.KEY
    r = requests.post(conf.ENDPOINT + '/ocarina/api/' + base_endpoint + '/', json=payload)
    print (r.json())
    return r.json()

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

def cli():
    config = get_config()
    print('''
                                 .@ 888S
                            ;@S8888:8%tX
 :XS.                 .;8: @8t88888t8888
X8%%S:              .8 8S888    :8.88S@:
8;8;888:        :@; 888888@8    88%888
%8:8%X8 t8. ;8 888.X8    88S@88888S %
 888S@@888  8@888@S8C    888    S%S:
 .@%888%@@t.888@@8@8@8::X88C   88 %
  ;S@X8@888S8X@@X8X88X888888%@888;
  Xt88X@8@@XX8S8X88@88888S888S.;
  t S888X8S8S8888X88@88%8@:@8%;
  :888X   @888    @88S88S888X
 .88;.     %X8    8@88S8X8:
 S8@S8@   8t8888%8@:8%S@88
 8%8;88888S@%.8S88;@8% %.
 :8.8    888    8XS:%:
 ::8St   88;   88S8;
   ;t 8X.8;%8 8%
''')
    print("Hello %s." % config["MAJORA_USER"])
