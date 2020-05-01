import os
import sys
import json
import hashlib
from datetime import datetime

import requests

from . import client
from . import version

def get_config(env=False):
    config = None

    if not env:
        config_path = os.path.expanduser("~/.ocarina")
        if os.path.exists(config_path):
            with open(config_path) as config_fh:
                config = json.load(config_fh)
                return config
        else:
            sys.stderr.write('''No configuration file found.\nCopy the command from below to initialise,\nthen edit the file and fill in the configration keys.\n''')
            sys.stderr.write('''echo '{"MAJORA_DOMAIN": "https:\\...\", "MAJORA_USER": "", "MAJORA_TOKEN": ""}' > ~/.ocarina\n''')
            sys.exit(1)
    else:
        config = {
            "MAJORA_DOMAIN": os.getenv("MAJORA_DOMAIN"),
            "MAJORA_USER": os.getenv("MAJORA_USER"),
            "MAJORA_TOKEN": os.getenv("MAJORA_TOKEN"),
        }
        if None in config.values():
            sys.stderr.write('''MAJORA_DOMAIN, MAJORA_USER, MAJORA_TOKEN must be set in your environment.\n''')
            sys.exit(1)
        return config


def emit(config, endpoint, payload, quiet=False, sudo_as=None):
    payload["username"] = config["MAJORA_USER"]
    payload["token"] = config["MAJORA_TOKEN"]
    payload["client_name"] = "ocarina"
    payload["client_version"] = version.__version__

    if sudo_as:
        payload["sudo_as"] = sudo_as

    del payload["quiet"]
    del payload["env"]
    angry = False
    if payload["angry"]:
        angry = True
    del payload["angry"]

    r = requests.post(config["MAJORA_DOMAIN"] + endpoint + '/',
            headers = {"Content-Type": "application/json", "charset": "UTF-8"},
            json = payload,
    )

    if r.status_code != 200:
        sys.stderr.write("Request" + "="*(80-len("Request ")) + '\n')
        payload["token"] = '*'*len(payload["token"])
        sys.stderr.write(json.dumps(payload, indent=4, sort_keys=True))
        sys.stderr.write("\nResponse" + "="*(80-len("Request ")) + '\n')
        sys.stderr.write("STATUS CODE %d\n" % r.status_code)
        sys.stderr.write(r.text)
        sys.exit(2)

    if not quiet:
        sys.stderr.write("Request" + "="*(80-len("Request ")) + '\n')
        payload["token"] = '*'*len(payload["token"])
        sys.stderr.write(json.dumps(payload, indent=4, sort_keys=True))

        sys.stderr.write("\nResponse" + "="*(80-len("Request ")) + '\n')
        sys.stderr.write(json.dumps(r.json(), indent=4, sort_keys=True))

    try:
        ret_json = r.json()
    except:
        sys.exit(3)

    if ret_json["errors"] > 0 and angry:
        sys.exit(1)

    return r.json()

def hashfile(path, start_clock=None, halg=hashlib.md5, bs=65536, force_hash=False, partial_limit=10737418240, partial_sample=0.2):
    start_time = datetime.now()

    hashed=False
    mod_time = os.path.getmtime(path)

    # This seems to be causing more trouble than anything else, so just hash everything for now
    # Best thing to do is probably attempt to fire a GET at the server and see if we have the last seen date
    #if mod_time >= int(start_clock.strftime("%s")) or force_hash:
    #    pass
    #else:
    #    # The file /probably/ hasn't change, so don't bother rehashing...
    #    ret = 'U'

    # For files less than partial_limit, just get on with it
    b_hashed = 0
    if os.path.getsize(path) <= partial_limit:
        f = open(path, 'rb')
        buff = f.read(bs)
        halg = halg()
        halg.update(buff)
        b_hashed = bs
        while len(buff) > 0:
            buff = f.read(bs)
            halg.update(buff)
            b_hashed += bs
        f.close()
        hashed=True
    else:
        # I want to ensure no hashing process takes longer than 5 minutes
        # Caveat: The longer the file is, the more sparse the samples are
        # NOTE This is probably a fucking terrible idea

        # Assuming a total of partial_sample bytes to sample for the hash,
        # find the skip size needed to evenly sample the file with bs blocks
        body_sample_size = 5.243e+8 # 500MiB
        ends_sample_size = 2.147e+9 # 2GiB
        body_consec_samples = math.ceil(body_sample_size/bs)
        ends_consec_samples = math.ceil(ends_sample_size/bs)

        file_size_body = int(os.path.getsize(path) - ((2*ends_sample_size) + (2*body_sample_size)))
        body_num_samples = int( (file_size_body * partial_sample) / body_sample_size) # number of body samples needed
        body_seek_size = int(file_size_body / body_num_samples)

        # Read the first blocks
        f = open(path, 'rb')
        halg = halg()
        for i in range(ends_consec_samples):
            buff = f.read(bs)
            halg.update(buff)
            b_hashed += bs

        # Now seek to the evenly distributed sample points across the body
        pos = f.tell() + body_sample_size
        for i in range(body_num_samples):
            f.seek(int(pos))
            for i in range(body_consec_samples):
                buff = f.read(bs)
                halg.update(buff)
                b_hashed += bs
            pos = f.tell() + body_seek_size

        f.seek(int(os.path.getsize(path) - ends_sample_size))
        while len(buff) > 0:
            buff = f.read(bs)
            halg.update(buff)
            b_hashed += bs
        f.close()
        hashed=True

    ret = '0'
    if hashed:
        ret = halg.hexdigest()

    end_time = datetime.now()
    hash_time = end_time - start_time
    #syslog.syslog('Hashed %s (~%.2fGB of %.2fGB in %s)' % (path, float(b_hashed) / 1e+9, float(os.path.getsize(path)) / 1e+9, str(hash_time)))

    return ret
