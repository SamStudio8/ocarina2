import os
import stat
import sys
import json
import hashlib
from datetime import datetime

import requests
from requests_oauthlib import OAuth2Session, TokenUpdated

from ffurf import FfurfConfig

from . import version

def check_and_warn_permissions(file_path):
    file_mode = os.stat(file_path).st_mode
    if bool(file_mode & (stat.S_IROTH | stat.S_IRGRP | stat.S_IWGRP | stat.S_IWOTH)): # if rw by group or other
        file_mode_oct = oct(file_mode)[-3:]
        sys.stderr.write("[WARN] Permissions %s for %s are too open and may allow other users to read or write your tokens!\n" % (file_mode_oct, file_path))

class OcarinaConfig(FfurfConfig):
    def __init__(self):
        super().__init__()
        self.add_config_key("MAJORA_DOMAIN", default_value="https://example.org/")
        self.add_config_key("MAJORA_USER")
        self.add_config_key("MAJORA_TOKEN", secret=True)
        self.add_config_key("MAJORA_TOKENS_FILE", default_value=os.path.expanduser("~/.ocarina-tokens"))
        self.add_config_key("CLIENT_ID", partial_secret=4)
        self.add_config_key("CLIENT_SECRET", secret=True)
        self.add_config_key("OCARINA_NO_BANNER", key_type=int, default_value=0)
        self.add_config_key("OCARINA_QUIET", key_type=int, default_value=0)

def get_config(env=False, profile=None):

    ffurf = OcarinaConfig()

    if not env:
        config_path = os.getenv("OCARINA_CONF_FILE")
        if not config_path:
            config_path = os.path.expanduser("~/.ocarina")

        if not os.path.exists(config_path):
            sys.stderr.write("No configuration file found.\nThe default configuration has been initialised at %s\nEdit the file and fill in the configration keys to use Ocarina.\n" % config_path)
            old_mask = os.umask(0o177) # mask to 600
            with open(config_path, 'w') as config_fh:
                config_fh.write(ffurf.to_json())
            os.umask(old_mask)
            sys.exit(78) #EX_CONFIG

        sys.stderr.write("[CONF] Loading config %s with profile %s\n" % (config_path, profile))
        check_and_warn_permissions(config_path)

        try:
            ffurf.from_json(config_path, profile=profile)
        except json.decoder.JSONDecodeError:
            sys.stderr.write("%s does not appear to be valid JSON" % config_path)
            sys.exit(78) #EX_CONFIG

    else:
        if profile:
            sys.stderr.write("[WARN] Cannot use --profile with --env, profile will be ignored.\n")

        ffurf.from_env()

        # Hack to keep legacy difference in env variable names working
        # without having to edit the real environment or make a backwards
        # incompatible change to the config
        if not ffurf["CLIENT_ID"]:
            try:
                ffurf.set_config_key("CLIENT_ID", os.getenv("MAJORA_CLIENT_ID"), source="env:MAJORA_CLIENT_ID")
                ffurf.set_config_key("CLIENT_SECRET", os.getenv("MAJORA_CLIENT_SECRET"), source="env:MAJORA_CLIENT_SECRET")
            except TypeError:
                pass

        if not ffurf.is_valid():
            sys.stderr.write("[FAIL] MAJORA_DOMAIN, MAJORA_USER, MAJORA_TOKEN must be set in your environment.\n")
            sys.exit(78) #EX_CONFIG

    if '~' in ffurf["MAJORA_TOKENS_FILE"]:
        ffurf.set_config_key("MAJORA_TOKENS_FILE", os.path.expanduser(ffurf["MAJORA_TOKENS_FILE"]), source=None, append_source=True)

    return ffurf

def oauth_load_tokens(tokens_path):
    if os.path.exists(tokens_path):
        check_and_warn_permissions(tokens_path)

        with open(tokens_path) as config_fh:
            try:
                config = json.load(config_fh)
                return config
            except json.decoder.JSONDecodeError:
                sys.stderr.write("%s does not appear to be valid JSON" % tokens_path)
                sys.exit(78) #EX_CONFIG
    else:
        return {}

def oauth_save_token(tokens_path, token):
    tokens = oauth_load_tokens(tokens_path)
    scope = " ".join(token["scope"])
    tokens[scope] = token

    old_mask = os.umask(0o177) # mask to 600
    with open(tokens_path, 'w') as config_fh:
        json.dump(tokens, config_fh)
    os.umask(old_mask)

def handle_oauth(config, oauth_scope, force_refresh=False, interactive=True):
    tokens = oauth_load_tokens(config["MAJORA_TOKENS_FILE"])
    if oauth_scope in tokens:
        # Check that token is valid
        if datetime.fromtimestamp(tokens[oauth_scope]["expires_at"]) <= datetime.now():
            if interactive:
                session, token = oauth_grant_to_token(config, oauth_scope)
                oauth_save_token(config["MAJORA_TOKENS_FILE"], token)
            else:
                # Return None in non-interactive as we can't get a token this way
                return None, None
        else:
            try:
                session = OAuth2Session(
                        client_id=config["CLIENT_ID"],
                        token=tokens[oauth_scope],
                        scope=oauth_scope,
                        auto_refresh_url=config["MAJORA_DOMAIN"]+"o/token/",
                        auto_refresh_kwargs={
                            "client_id": config["CLIENT_ID"],
                            "client_secret": config["CLIENT_SECRET"],
                        },
                )
            except TokenUpdated as e:
                oauth_save_token(config["MAJORA_TOKENS_FILE"], token)

            if force_refresh:
                #TODO This would actually force a double refresh in the case where the session is update automatically but whatever
                refresh_params = {
                    "client_id": config["CLIENT_ID"],
                    "client_secret": config["CLIENT_SECRET"],
                }
                token = session.refresh_token(config["MAJORA_DOMAIN"]+"o/token/", **refresh_params)
                oauth_save_token(config["MAJORA_TOKENS_FILE"], token)

            token = tokens[oauth_scope]
    else:
        # No scoped token
        if interactive:
            session, token = oauth_grant_to_token(config, oauth_scope)
            oauth_save_token(config["MAJORA_TOKENS_FILE"], token)
        else:
            # Return None in non-interactive as we can't get a token this way
            return None, None

    return session, token

def oauth_grant_to_token(config, oauth_scope):
    #TODO Very particular about the URL here - need to mitigate risk of //
    oauth = OAuth2Session(client_id=config["CLIENT_ID"], redirect_uri=config["MAJORA_DOMAIN"]+"o/callback/", scope=oauth_scope)
    print("Please request a grant via:")
    url, state = oauth.authorization_url(config["MAJORA_DOMAIN"]+"o/authorize/", approval_prompt="auto")
    print(url)
    authorization_response = ""
    attempt = 1
    while not authorization_response.startswith(config["MAJORA_DOMAIN"]):
        if attempt == 4:
            print("Giving up on OAuth authentication and aborting. Try again later.\n")
            sys.exit(75) #EX_TEMPFAIL
        elif attempt > 1:
            print("***\nSorry, your response doesn't appear to start with the address of the callback.\nPlease paste the entire URL for the authorization page as seen in your browser bar.\n***\n")
        authorization_response = input('Enter the full callback URL as seen in your browser window\n')
        attempt += 1
    token = oauth.fetch_token(config["MAJORA_DOMAIN"]+"o/token/", authorization_response=authorization_response, client_secret=config["CLIENT_SECRET"])
    return oauth, token

def emit(ocarina, endpoint, payload, quiet=False):

    params = payload.get("params")
    if params:
        del payload["params"]

    payload["client_name"] = "ocarina"
    payload["client_version"] = version.__version__

    if ocarina.sudo_as:
        payload["sudo_as"] = ocarina.sudo_as

    if not quiet:
        quiet = ocarina.quiet

    if "quiet" in payload:
        del payload["quiet"]
    if "env" in payload:
        del payload["env"]

    angry = False
    if "angry" in payload:
        if payload["angry"]:
            angry = True
            del payload["angry"]


    payload["username"] = ocarina.config["MAJORA_USER"]

    request_type = "POST"
    if type(endpoint) == dict:
        # OAuth and v3 endpoints are defined with a dict so we can catch them here
        if "scope" in endpoint:
            ocarina.oauth_scope = endpoint["scope"] # store the last scope for polling tasks to access later
            if not ocarina.oauth and endpoint["version"] in [0,3]:
                sys.stderr.write("--oauth is required with experimental or v3 API endpoints")
                sys.exit(64) #EX_USAGE
        request_type = endpoint["type"]
        endpoint = endpoint["endpoint"]

    if not ocarina.oauth:
        # Old school non-OAuth and v2 APIs POST here
        payload["token"] = ocarina.config["MAJORA_TOKEN"]
        r = requests.post(ocarina.config["MAJORA_DOMAIN"] + endpoint + '/',
                headers = {
                    "Content-Type": "application/json",
                    "charset": "UTF-8",
                    "User-Agent": "%s %s" % (payload["client_name"], payload["client_version"]),
                },
                json = payload,
        )
    else:
        # OAuth and v3 endpoints drop to here
        # Always refresh the session to ensure a token change does not disrupt polling tasks
        ocarina.oauth_session, ocarina.oauth_token = handle_oauth(ocarina.config, ocarina.oauth_scope, interactive=ocarina.interactive)

        if not ocarina.oauth_session or not ocarina.oauth_token:
            # Looks like oauth failed, this should just trigger a 400
            print("Unexpected OAuth Error. Try refreshing all tokens with `ocarina oauth refresh`.")
            sys.exit(75) #EX_TEMPFAIL

        payload["token"] = "OAUTH"
        if request_type == "POST":
            r = ocarina.oauth_session.post(ocarina.config["MAJORA_DOMAIN"] + endpoint + '/',
                    headers = {
                        "Content-Type": "application/json",
                        "charset": "UTF-8",
                        "User-Agent": "%s %s" % (payload["client_name"], payload["client_version"]),
                    },
                    json = payload,
                    stream = ocarina.stream,
            )
        elif request_type == "GET":
            r = ocarina.oauth_session.get(ocarina.config["MAJORA_DOMAIN"] + endpoint + '/',
                    headers = {
                        "charset": "UTF-8",
                        "User-Agent": "%s %s" % (payload["client_name"], payload["client_version"]),
                    },
                    params = params,
                    stream = ocarina.stream,
            )

    if r.status_code != 200:
        sys.stderr.write("Request" + "="*(80-len("Request ")) + '\n')
        payload["token"] = '*'*len(payload["token"])
        sys.stderr.write(json.dumps(payload, indent=4, sort_keys=True))
        sys.stderr.write("\nResponse" + "="*(80-len("Request ")) + '\n')
        sys.stderr.write("STATUS CODE %d\n" % r.status_code)
        sys.stderr.write(r.text + '\n')

        if r.status_code == 400 or r.status_code == 403:
            # Bad request 400 or fobidden 403
            sys.exit(77) #EX_NOPERM
        elif r.status_code == 500:
            # Server error 500
            sys.exit(69) #EX_UNAVAILABLE
        elif r.status_code == 429 or r.status_code == 503:
            # Too many reqs 429 or unavailable 503
            sys.exit(75) #EX_TEMPFAIL
        else:
            # Otherwise assume we fucked it and issue general 70
            sys.exit(70) #EX_SOFTWARE

    if not quiet:
        sys.stderr.write("Request" + "="*(80-len("Request ")) + '\n')
        payload["token"] = '*'*len(payload["token"])
        sys.stderr.write(json.dumps(payload, indent=4, sort_keys=True))

        sys.stderr.write("\nResponse" + "="*(80-len("Request ")) + '\n')
        sys.stderr.write(json.dumps(r.json(), indent=4, sort_keys=True) + '\n')

    try:
        ret_json = r.json()
    except:
        sys.exit(69) #EX_UNAVAILABLE

    if ret_json["errors"] > 0 and angry:
        sys.exit(1) #EX_GENERAL

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
