import os
import sys

import json
from . import util

import argparse

CLIENT_VERSION = "0.0.3"
ENDPOINTS = {
        "api.artifact.biosample.add": "/api/v2/artifact/biosample/add/",
        "api.artifact.library.add": "/api/v2/artifact/library/add/",
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


    library_parser = subparsers.add_parser("library", help="add a sequencing library by providing fields via the CLI")
    lpg = library_parser.add_mutually_exclusive_group(required=True)
    lpg.add_argument("--biosamples", nargs='+')
    lpg.add_argument("--biosample", action='append', nargs=4,
            metavar=('central_sample_id', 'library_source', 'library_selection', 'library_strategy'))

    library_parser.add_argument("--apply-all-library", nargs=3,
            metavar=('library_source', 'library_selection', 'library_strategy'))
    library_parser.add_argument("--library-layout-config", required=True)
    library_parser.add_argument("--library-name", required=True)
    library_parser.add_argument("--library-seq-kit", required=True)
    library_parser.add_argument("--library-seq-protocol", required=True)
    library_parser.add_argument("--library-layout-insert-length")
    library_parser.add_argument("--library-layout-read-length")
    library_parser.set_defaults(func=wrap_library_emit)

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

def wrap_library_emit(args):
    v_args = vars(args)
    del v_args["func"]

    print(args)
    print(v_args)

    if args.biosample:
        submit_biosamples = []
        for entry in args.biosample:
            submit_biosamples.append({
                "central_sample_id": entry[0],
                "library_source": entry[1],
                "library_selection": entry[1],
                "library_strategy": entry[2],
            })
        del v_args["biosample"]

    elif args.biosamples:
        if not args.apply_all_library:
            print("Use --apply-all-library with --biosamples")
            sys.exit(2)

        submit_biosamples = []
        for entry in args.biosamples:
            submit_biosamples.append({
                "central_sample_id": entry,
                "library_source": args.apply_all_library[0],
                "library_selection": args.apply_all_library[1],
                "library_strategy": args.apply_all_library[2],
            })
        del v_args["apply_all_library"]
        del v_args["biosamples"]

    v_args["biosamples"] = submit_biosamples
    util.emit(ENDPOINTS["api.artifact.library.add"], v_args)

