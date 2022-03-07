
```
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
```

# ocarina2
Ocarina is a simple Python requests program for shouting at the [Majora](https://github.com/SamStudio8/majora) API.
This repo is for `ocarina2` and is designed to interact with `majora2`. It will not work with a future incarnation of Majora.
Development of `ocarina2` serves only to maintain ongoing research use by COG-UK.

## Install

```
pip install git+https://github.com/climb-covid/ocarina2.git
```

## Configuration
On first run, `ocarina` will give you a command to generate the config file.
Edit the configuration and supply to provide the required parameters:

* `MAJORA_DOMAIN` the base URL of the Majora instance to send requests to
* `MAJORA_USER` your username on Majora
* `MAJORA_TOKEN` your API key, you can get this from your profile
* `CLIENT_ID` your OAuth client ID
* `CLIENT_SECRET` your OAuth client secret
* `OCARINA_QUIET` set to anything non-zero (`0`) to suppress all non-output information
* `OCARINA_NO_BANNER` set to anything non-zero (`0`) to suppress the large welcoming ocarina
* `MAJORA_TOKENS_FILE` a location to save OAuth refresh tokens

Alternatively, you can specify `--env` and set these configuration parameters in your environment.

## Profile based configuration

If you are using `majora-prod` and `majora-magenta` you can specify an `OCARINA_CONF_FILE` environment variable (without `--env`) to load a JSON configuration of profiles instead.
The keys are the same as above, but are nested in a `profile` object as below:

```
{
  "profile": {
    "test": {
        "MAJORA_DOMAIN": "https://majora-test.eu/",
        "MAJORA_USER": "test-s.nicholls",
        "MAJORA_TOKEN": "oauth",
        "CLIENT_ID": "...",
        "CLIENT_SECRET": "...",
        "OCARINA_NO_BANNER": 0,
        "OCARINA_QUIET": 0,
        "MAJORA_TOKENS_FILE": "/path/for/test/tokenz"
    },
    "not-test": {
        "MAJORA_DOMAIN": "https://majora.eu/",
        "MAJORA_USER": "real-s.nicholls",
        "MAJORA_TOKEN": "oauth",
        "CLIENT_ID": "...",
        "CLIENT_SECRET": "...",
        "OCARINA_NO_BANNER": 0,
        "OCARINA_QUIET": 0,
        "MAJORA_TOKENS_FILE": "/path/for/real/tokenz"
    }
}
```

## Documentation

For Ocarina command line examples, [see the new Majora documentation](https://samstudio8.github.io/majora-docs/).
