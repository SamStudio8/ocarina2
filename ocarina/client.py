import os
import sys

import json
from . import util
from . import parsers

import argparse

ENDPOINTS = {
        "api.artifact.biosample.add": "/api/v2/artifact/biosample/add/",
        "api.artifact.library.add": "/api/v2/artifact/library/add/",
        "api.process.sequencing.add": "/api/v2/process/sequencing/add/",
        "api.artifact.file.add": "/api/v2/artifact/file/add/",
        "api.meta.tag.add": "/api/v2/meta/tag/add/",

        "api.artifact.biosample.get": "/api/v2/artifact/biosample/get/",
        "api.process.sequencing.get": "/api/v2/process/sequencing/get/",
}


def cli():
    config = util.get_config()

    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--quiet", help="suppress the large welcoming ocarina", action="store_true")

    action_parser = parser.add_subparsers()
    put_parser = action_parser.add_parser("put")
    put_parser.add_argument("-m", "--metadata", action='append', nargs=3, metavar=('tag', 'key', 'value'))

    subparsers = put_parser.add_subparsers(title="actions")

    biosample_parser = subparsers.add_parser("biosample", parents=[put_parser], add_help=False,
            help="add a single biosample by providing fields via the CLI")
    biosample_parser.add_argument("--adm1", required=True)
    biosample_parser.add_argument("--central-sample-id", "--coguk-sample-id", required=True)

    bsp_date = biosample_parser.add_mutually_exclusive_group(required=True)
    bsp_date.add_argument("--collection-date")
    bsp_date.add_argument("--received-date")

    biosample_parser.add_argument("--source-age", required=True)
    biosample_parser.add_argument("--source-sex", required=True)
    biosample_parser.add_argument("--secondary-accession", "--gisaid-accession")
    biosample_parser.add_argument("--secondary-identifier", "--gisaid-identifier")
    biosample_parser.add_argument("--adm2")
    biosample_parser.add_argument("--adm2-private")
    biosample_parser.add_argument("--biosample-source-id")
    biosample_parser.add_argument("--collecting-org")
    biosample_parser.add_argument("--root-sample-id")
    biosample_parser.add_argument("--sample-type-collected")
    biosample_parser.add_argument("--sample-type-received")
    biosample_parser.add_argument("--sender-sample-id", "--local-sample-id")
    biosample_parser.add_argument("--swab-site")
    biosample_parser.set_defaults(func=wrap_single_biosample_emit)


    library_parser = subparsers.add_parser("library", parents=[put_parser], add_help=False,
            help="add a sequencing library by providing fields via the CLI")
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
    library_parser.add_argument("--force-biosamples", action="store_true")
    library_parser.set_defaults(func=wrap_library_emit)


    sequencing_parser = subparsers.add_parser("sequencing", parents=[put_parser], add_help=False,
            help="add a single sequencing run by providing fields via the CLI")
    sequencing_parser.add_argument("--library-name", required=True)
    sequencing_parser.add_argument("--run-group", required=False)

    spg = sequencing_parser.add_mutually_exclusive_group(required=True)
    spg.add_argument("--sequencing-id") #TODO allow for both?
    spg.add_argument("--run-name")

    sequencing_parser.add_argument("--instrument-make", required=True)
    sequencing_parser.add_argument("--instrument-model", required=True)
    sequencing_parser.add_argument("--flowcell-type")
    sequencing_parser.add_argument("--flowcell-id")
    sequencing_parser.add_argument("--start-time")
    sequencing_parser.add_argument("--end-time")
    sequencing_parser.set_defaults(func=wrap_sequencing_emit)


    digitalresource_parser = subparsers.add_parser("file", parents=[put_parser], add_help=False,
            help="register a local digital resource (file) over the Majora API")
    digitalresource_parser.add_argument("--bridge-artifact", "--biosample", required=False)
    digitalresource_parser.add_argument("--source-artifact", "--source-file", required=False, nargs='+')
    digitalresource_parser.add_argument("--source-group", required=False, nargs='+')
    digitalresource_parser.add_argument("--pipeline", required=True, nargs=4,
            metavar=["pipe_id", "pipe_category", "pipe_name", "pipe_version"])
    digitalresource_parser.add_argument("--node", required=False)
    digitalresource_parser.add_argument("--path", required=True)
    digitalresource_parser.add_argument("--type", required=True) #TODO --reads | --consensus | --alignment?
    digitalresource_parser.add_argument("--i-have-bad-files", action="store_true")
    digitalresource_parser.add_argument("--full-path", action="store_true")
    digitalresource_parser.add_argument("--no-user", action="store_true")
    digitalresource_parser.set_defaults(func=wrap_digitalresource_emit)


    #pipeline_parser = subparsers.add_parser("pipe", parents=[parser], add_help=False,
    #        help="Register a pipeline over the Majora API"))

    tag_parser = subparsers.add_parser("tag", parents=[put_parser], add_help=False,
            help="Tag an artifact or process with some metadata")
    tpg = tag_parser.add_mutually_exclusive_group(required=True)
    tpg.add_argument("--artifact")
    tpg.add_argument("--group")
    tpg.add_argument("--process")
    tag_parser.set_defaults(func=wrap_tag_emit)


    get_parser = action_parser.add_parser("get")
    get_subparsers = get_parser.add_subparsers(title="actions")

    get_biosample_parser = get_subparsers.add_parser("biosample", parents=[get_parser], add_help=False,
            help="fetch a biosample")
    get_biosample_parser.add_argument("--central-sample-id", "--coguk-sample-id", required=True)
    get_biosample_parser.set_defaults(func=wrap_get_biosample)

    get_sequencing_parser = get_subparsers.add_parser("sequencing", parents=[get_parser], add_help=False,
            help="fetch a sequencing run")
    get_sequencing_parser.add_argument("--run-name", required=True)
    get_sequencing_parser.set_defaults(func=wrap_get_sequencing)

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
        metadata = {}
        if hasattr(args, "metadata") and args.metadata:
            for entry in args.metadata:
                key, name, value = entry
                if key not in metadata:
                    metadata[key] = {}
                metadata[key][name] = value
        args.func(args, metadata)

def wrap_single_biosample_emit(args, metadata={}):
    v_args = vars(args)
    del v_args["func"]

    v_args["metadata"] = metadata
    payload = {"biosamples": [
        v_args,
    ]}
    util.emit(ENDPOINTS["api.artifact.biosample.add"], payload)

def wrap_get_biosample(args, metadata={}):
    v_args = vars(args)
    del v_args["func"]
    util.emit(ENDPOINTS["api.artifact.biosample.get"], v_args)
def wrap_get_sequencing(args, metadata={}):
    v_args = vars(args)
    del v_args["func"]
    util.emit(ENDPOINTS["api.process.sequencing.get"], v_args)

def wrap_sequencing_emit(args, metadata={}):
    v_args = vars(args)
    del v_args["func"]

    payload = {
        "metadata": metadata,
        "library_name": v_args["library_name"],
        "run_group": v_args["run_group"],
        "runs": [
            v_args,
        ]
    }
    util.emit(ENDPOINTS["api.process.sequencing.add"], payload)

def wrap_library_emit(args, metadata={}):
    v_args = vars(args)
    del v_args["func"]

    if args.biosample:
        submit_biosamples = []
        for entry in args.biosample:
            submit_biosamples.append({
                "central_sample_id": entry[0],
                "library_source": entry[1],
                "library_selection": entry[2],
                "library_strategy": entry[3],
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

    v_args["metadata"] = metadata
    v_args["biosamples"] = submit_biosamples
    util.emit(ENDPOINTS["api.artifact.library.add"], v_args)

def wrap_digitalresource_emit(args, metadata={}):
    v_args = vars(args)

    path = os.path.abspath(v_args["path"])
    if not os.path.exists(path):
        print("Path does not exist")
        sys.exit(2)
    if not os.path.isfile(path):
        print("Path does not appear to be a file")
        sys.exit(2)

    resource_hash = util.hashfile(path, force_hash=True)
    resource_size = os.path.getsize(path)
    #node_uuid = "..."
    path = path
    current_name = os.path.basename(path)
    extension = current_name.split('.')[-1]

    warnings_found = False
    song = parsers.get_parser_for_type(path)
    if song:
        for check_name, check  in song.check_integrity().items():
            if check.get("result"):
                print("[WARN] %s %s" % (current_name, check.get("msg", "")))
                warnings_found = True
        metadata.update(song.get_metadata())
        extension = song.extension
    if warnings_found and not args.i_have_bad_files:
        print("[FAIL] Problems with your file were detected. If you don't care, run this command again with --i-have-bad-files. I'll know it was you, though.")
        sys.exit(3)

    path = path.split(os.path.sep)
    if not args.full_path:
        # Send a single directory and filename
        path = path[-2:]
        if not args.no_user:
            config = util.get_config()
            path = [config["MAJORA_USER"]] + path
        path = ['null'] + path # dont ask
    path = os.path.sep.join(path)

    payload = {
        #"node_uuid": node_uuid,
        "node_name": args.node,
        "path": path,
        "sep": os.path.sep,
        "current_fext": extension,
        "current_name": os.path.basename(path),
        "current_hash": resource_hash,
        "current_size": resource_size,
        "resource_type": args.type,
        "metadata": metadata,

        "pipe_id": args.pipeline[0],
        "pipe_kind": args.pipeline[1],
        "pipe_name": args.pipeline[2],
        "pipe_version": args.pipeline[3],

        "source_group": args.source_group,
        "source_artifact": args.source_artifact,
        "bridge_artifact": args.bridge_artifact,
    }
    util.emit(ENDPOINTS["api.artifact.file.add"], payload)

def wrap_tag_emit(args, metadata={}):
    v_args = vars(args)
    del v_args["func"]

    v_args["metadata"] = metadata
    util.emit(ENDPOINTS["api.meta.tag.add"], v_args)
