import os
import sys

import json
from . import util

import argparse

CLIENT_VERSION = "0.0.3"
ENDPOINTS = {
        "api.artifact.biosample.add": "/api/v2/artifact/biosample/add/",
        "api.process.sequencing.add": "/api/v2/process/sequencing/add/",
}


def cli():
    config = util.get_config()

    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--quiet", help="suppress the large welcoming ocarina", action="store_true")
    subparsers = parser.add_subparsers()

    biosample_parser = subparsers.add_parser("biosample", help="add a single biosample by providing fields via the CLI")
    biosample_parser.add_argument("--adm1", required=True)
    biosample_parser.add_argument("--central-sample-id", "--coguk-sample-id", required=True)
    biosample_parser.add_argument("--collection-date", required=True)
    biosample_parser.add_argument("--source-age", required=True)
    biosample_parser.add_argument("--source-sex", required=True)
    biosample_parser.add_argument("--override-heron", action="store_true")
    biosample_parser.add_argument("--secondary-accession", "--gisaid-accession")
    biosample_parser.add_argument("--secondary-identifier", "--gisaid-identifier")
    biosample_parser.add_argument("--adm2")
    biosample_parser.add_argument("--biosample-source-id")
    biosample_parser.add_argument("--collecting-org")
    biosample_parser.add_argument("--root-sample-id")
    biosample_parser.add_argument("--sample-type-collected")
    biosample_parser.add_argument("--sample-type-received")
    biosample_parser.add_argument("--sender-sample-id", "--local-sample-id")
    biosample_parser.add_argument("--swab-site")
    biosample_parser.set_defaults(func=wrap_single_biosample_emit)

    args = parser.parse_args()
    if not args.quiet:
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

    if hasattr(args, "func"):
        args.func(args)

def wrap_single_biosample_emit(args):
    v_args = vars(args)
    del v_args["func"]

    payload = {"biosamples": [
        v_args,
    ]}
    util.emit(ENDPOINTS["api.artifact.biosample.add"], payload)
