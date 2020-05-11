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
        "api.meta.metric.add": "/api/v2/meta/metric/add/",
        "api.meta.qc.add": "/api/v2/meta/qc/add/",

        "api.pag.qc.get": "/api/v2/pag/qc/get/",
        "api.pag.accession.add": "/api/v2/pag/accession/add/",

        "api.artifact.biosample.get": "/api/v2/artifact/biosample/get/",
        "api.process.sequencing.get": "/api/v2/process/sequencing/get/",

        "api.majora.summary.get": "/api/v2/majora/summary/get/",
        "api.majora.task.get": "/api/v2/majora/task/get/",

        "api.majora.task.delete": "/api/v2/majora/task/delete/",
}


def cli():

    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--quiet", help="suppress the large welcoming ocarina", action="store_true")
    parser.add_argument("--env", help="use env vars instead of ~/.ocarina", action="store_true")
    parser.add_argument("--angry", help="exit if API returns errors > 0", action="store_true", default=False)

    action_parser = parser.add_subparsers()
    put_parser = action_parser.add_parser("put")
    put_parser.add_argument("-m", "--metadata", action='append', nargs=3, metavar=('tag', 'key', 'value'))
    put_parser.add_argument("--metric", action='append', nargs=3, metavar=('tag', 'key', 'value'))
    put_parser.add_argument("--sudo-as", required=False)

    subparsers = put_parser.add_subparsers(title="actions")

    biosample_parser = subparsers.add_parser("biosample", parents=[put_parser], add_help=False,
            help="add a single biosample by providing fields via the CLI")
    biosample_parser.add_argument("--adm1", required=True)
    biosample_parser.add_argument("--central-sample-id", "--coguk-sample-id", required=True)

    bsp_date = biosample_parser.add_mutually_exclusive_group(required=True)
    bsp_date.add_argument("--collection-date")
    bsp_date.add_argument("--received-date")

    biosample_parser.add_argument("--source-age")
    biosample_parser.add_argument("--source-sex")
    biosample_parser.add_argument("--source-category")
    biosample_parser.add_argument("--source-setting")
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
    biosample_parser.add_argument("--sampling-strategy")
    biosample_parser.set_defaults(func=wrap_single_biosample_emit)


    library_parser = subparsers.add_parser("library", parents=[put_parser], add_help=False,
            help="add a sequencing library by providing fields via the CLI")
    lpg = library_parser.add_mutually_exclusive_group(required=True)
    lpg.add_argument("--biosamples", nargs='+')
    lpg.add_argument("--biosample", action='append', nargs=6,
            metavar=('central_sample_id', 'library_source', 'library_selection', 'library_strategy', 'library_protocol', 'library_primers'))

    library_parser.add_argument("--apply-all-library", nargs=5,
            metavar=('library_source', 'library_selection', 'library_strategy', 'library_protocol', 'library_primers'))
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
    digitalresource_parser.add_argument("--publish-group", required=False)
    digitalresource_parser.add_argument("--source-group", required=False, nargs='+')
    digitalresource_parser.add_argument("--pipeline", required=True, nargs=4,
            metavar=["pipe_hook", "pipe_category", "pipe_name", "pipe_version"])
    digitalresource_parser.add_argument("--node", required=False)
    digitalresource_parser.add_argument("--path", required=True)
    digitalresource_parser.add_argument("--type", required=True) #TODO --reads | --consensus | --alignment?
    digitalresource_parser.add_argument("--i-have-bad-files", action="store_true")
    digitalresource_parser.add_argument("--full-path", action="store_true")
    digitalresource_parser.add_argument("--no-user", action="store_true")
    digitalresource_parser.add_argument("--artifact-uuid")
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


    metric_parser = subparsers.add_parser("metric", parents=[put_parser], add_help=False,
            help="Add metrics to an artifact")
    mpg = metric_parser.add_mutually_exclusive_group(required=True)
    mpg.add_argument("--artifact")
    mpg.add_argument("--artifact-path")
    metric_parser.set_defaults(func=wrap_metric_emit)


    qc_parser = subparsers.add_parser("qc", parents=[put_parser], add_help=False,
            help="Apply QC to a PAG")
    qc_parser.add_argument("--publish-group", required=True)
    qc_parser.add_argument("--test-name", required=True)
    qc_parser.add_argument("--test-version", type=int, required=True)
    qc_parser.set_defaults(func=wrap_qc_emit)


    publish_parser = subparsers.add_parser("publish", parents=[put_parser], add_help=False,
            help="Add a public accession to a published artifact group")
    publish_parser.add_argument("--publish-group", required=True)
    publish_parser.add_argument("--contains", action="store_true")
    publish_parser.add_argument("--service", required=True)
    publish_parser.add_argument("--accession", required=True)
    publish_parser.add_argument("--accession2", required=False)
    publish_parser.add_argument("--accession3", required=False)
    publish_parser.add_argument("--public", action="store_true")
    publish_parser.set_defaults(func=wrap_publish_emit)


    get_parser = action_parser.add_parser("get")
    get_parser.add_argument("--task-id", help="Request the result from the Majora task endpoint")
    get_parser.add_argument("--task-del", help="Destroy the task result if this command finishes successfully", action="store_true")
    get_subparsers = get_parser.add_subparsers(title="actions")

    get_biosample_parser = get_subparsers.add_parser("biosample", parents=[get_parser], add_help=False,
            help="fetch a biosample")
    get_biosample_parser.add_argument("--central-sample-id", "--coguk-sample-id", required=True)
    get_biosample_parser.set_defaults(func=wrap_get_biosample)

    get_sequencing_parser = get_subparsers.add_parser("sequencing", parents=[get_parser], add_help=False,
            help="fetch a sequencing run")
    get_sequencing_parser.add_argument("--run-name", required=True, nargs='+')
    get_sequencing_parser.add_argument("--tsv", action="store_true")
    get_sequencing_parser.add_argument("--tsv-show-dummy", action="store_true")
    get_sequencing_parser.set_defaults(func=wrap_get_sequencing)


    get_pag_parser = get_subparsers.add_parser("pag", parents=[get_parser], add_help=False,
            help="Get all PAGs that have passed a QC test")
    get_pag_parser.add_argument("--test-name", required=True)

    get_pag_parser.add_argument("--pass", action="store_true")
    get_pag_parser.add_argument("--fail", action="store_true")

    get_pag_parser.add_argument("--public", action="store_true")
    get_pag_parser.add_argument("--private", action="store_true")

    get_pag_parser.add_argument("--ls-files", action="store_true")
    get_pag_parser.add_argument("--ofield", nargs=3, metavar=("field", "as", "default"), action="append")
    get_pag_parser.set_defaults(func=wrap_get_qc)


    get_summary_parser = get_subparsers.add_parser("summary", parents=[get_parser], add_help=False,
            help="Get summary metrics")
    get_summary_parser.add_argument("--gte-date")
    get_summary_parser.add_argument("--md", action="store_true")
    get_summary_parser.set_defaults(func=wrap_get_summary)


    del_parser = action_parser.add_parser("del")
    del_subparsers = del_parser.add_subparsers(title="actions")

    del_task_parser = del_subparsers.add_parser("task", parents=[del_parser], add_help=False,
            help="Delete the results of a Celery task")
    del_task_parser.add_argument("--task-id", required=True)
    del_task_parser.set_defaults(func=wrap_del_task)

    args = parser.parse_args()
    config = util.get_config(args.env)
    if not args.quiet:
        sys.stderr.write('''
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
        sys.stderr.write("Hello %s.\n" % config["MAJORA_USER"])

    if hasattr(args, "func"):
        metadata = {}
        if hasattr(args, "metadata") and args.metadata:
            for entry in args.metadata:
                key, name, value = entry
                if key not in metadata:
                    metadata[key] = {}
                metadata[key][name] = value
        metrics = {}
        if hasattr(args, "metric") and args.metric:
            for entry in args.metric:
                key, name, value = entry

                ks = key.split('.')
                if len(ks) == 1:
                    k_namespace, k_record = ks[0], None
                else:
                    k_namespace, k_record = ks
                if k_namespace not in metrics:
                    metrics[k_namespace] = {}

                if k_record:
                    if "records" not in metrics[k_namespace]:
                        metrics[k_namespace]["records"] = {}
                    if k_record not in metrics[k_namespace]["records"]:
                        metrics[k_namespace]["records"][k_record] = {}
                    metrics[k_namespace]["records"][k_record][name] = value
                else:
                    metrics[k_namespace][name] = value
        args.func(args, config, metadata=metadata, metrics=metrics)

def wrap_single_biosample_emit(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]
    del v_args["metric"]

    v_args["metadata"] = metadata
    v_args["metrics"] = metrics
    payload = {"biosamples": [
        v_args,
    ]}
    util.emit(config, ENDPOINTS["api.artifact.biosample.add"], payload, quiet=args.quiet, sudo_as=args.sudo_as)

def wrap_get_biosample(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]
    util.emit(config, ENDPOINTS["api.artifact.biosample.get"], v_args, quiet=args.quiet)

def wrap_get_summary(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]
    j = util.emit(config, ENDPOINTS["api.majora.summary.get"], v_args, quiet=args.quiet)

    if args.md:
        if len(j["get"]["site_qc"]) >= 1:
            print("| Site | Count | Pass | Fail |")
            print("|------|------:|-----:|-----:|")
            for group in j["get"]["site_qc"]:
                print("| %s | %d | %d (%.2f%%) | %d (%.2f%%) |" % (
                    group["site"],
                    group["count"],
                    group["pass_count"],
                    group["pass_count"]/group["count"] * 100,
                    group["fail_count"],
                    group["fail_count"]/group["count"] * 100,
                ))

def wrap_get_task(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]
    j = util.emit(config, ENDPOINTS["api.majora.task.get"], v_args, quiet=args.quiet)

def wrap_del_task(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]
    j = util.emit(config, ENDPOINTS["api.majora.task.delete"], v_args, quiet=args.quiet)

def wrap_get_qc(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]

    if args.task_id:
        j = util.emit(config, ENDPOINTS["api.majora.task.get"], v_args, quiet=args.quiet)
        #TODO move this to part of emit
        if j.get("task", {}).get("state", "") != "SUCCESS":
            return
    else:
        j = util.emit(config, ENDPOINTS["api.pag.qc.get"], v_args, quiet=args.quiet)

    if args.ls_files:
        if len(j["get"]) >= 1:
            for pag in j["get"]:
                if "Digital Resource" in j["get"][pag]["artifacts"]:
                    for dra in j["get"][pag]["artifacts"]["Digital Resource"]:
                        sys.stdout.write("\t".join([
                            pag,
                            dra["current_kind"],
                            dra["current_path"],
                            dra["current_hash"],
                            str(dra["current_size"]),
                            j["get"][pag]["status"],
                        ]) + '\n')
    elif args.ofield:
        if len(j["get"]) >= 1:
            for pag in j["get"]:
                # Flatten the PAG to unique distinguished objects
                metadata = {k:v for k,v in j["get"][pag].items() if type(v) != dict and type(v) != list}
                for artifact_g in j["get"][pag]["artifacts"]:
                    for artifact in j["get"][pag]["artifacts"][artifact_g]:
                        for k, v in artifact.items():
                            if k not in metadata and type(v) != dict and type(v) != list:
                                metadata[k] = v
                            elif k in metadata:
                                del metadata[k] # unique stuff only for now
                        if "metadata" in artifact:
                            for namespace in artifact["metadata"]:
                                for mkey, mvalue in artifact["metadata"][namespace].items():
                                    mkey = "%s.%s" % (namespace, mkey)
                                    if mkey not in metadata:
                                        metadata[mkey] = mvalue
                                    else:
                                        del metadata[mkey]

                row = {}
                for ofield in args.ofield:
                    field, as_, default = ofield
                    if field in metadata and metadata[field] is not None:
                        v = metadata[field]
                    else:
                        v = default
                    print(as_, v)

    if args.task_del and j.get("task", {}).get("state", "") == "SUCCESS":
        j = util.emit(config, ENDPOINTS["api.majora.task.delete"], v_args, quiet=args.quiet)

def wrap_get_sequencing(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]
    j = util.emit(config, ENDPOINTS["api.process.sequencing.get"], v_args, quiet=args.quiet)

    if v_args["tsv"]:
        i = 0
        header = None

        if len(j["get"]) >= 1:
            all_possible_meta_keys = set([])
            for run in j["get"]:
                for l in j["get"][run]["libraries"]:
                    if l["metadata"]:
                        flat_meta = {}
                        for tag in l["metadata"]:
                            for name in l["metadata"][tag]:
                                flat_meta["meta.%s.%s" % (tag, name)] = l["metadata"][tag][name]
                                all_possible_meta_keys.add("meta.%s.%s" % (tag, name))
                        l.update(flat_meta)
                    try:
                        del l["metadata"]
                    except:
                        pass

            for run in j["get"]:
                row_master = j["get"][run]
                libraries = row_master.get("libraries")
                del row_master["libraries"]

                for l in libraries:
                    lib_master = l
                    biosamples = lib_master["biosamples"]
                    del lib_master["biosamples"]

                    for mk in all_possible_meta_keys:
                        if mk not in lib_master:
                            lib_master[mk] = None

                    for b in biosamples:
                        if not b.get("adm0") and not v_args["tsv_show_dummy"]:
                            sys.stderr.write("Skipping row: %s.%s.%s as it does not have a complete set of headers...\n" % (run, l["library_name"], b["central_sample_id"]))
                            continue
                        try:
                            b["biosample_source_id"] = b["biosample_sources"][0]["biosample_source_id"]
                        except:
                            b["biosample_source_id"] = None

                        try:
                            del b["biosample_sources"]
                        except:
                            pass

                        row = {}
                        row.update(row_master)
                        row.update(lib_master)
                        row.update(b)

                        fields = []
                        for f in sorted(row):
                            fields.append(str(row[f]))

                        if i == 0:
                            header = sorted(row)
                            print("\t".join(header))
                        if len(fields) != len(header):
                            sys.stderr.write("Skipping row: %s.%s.%s as it does not have a complete set of headers...\n" % (run, l["library_name"], b["central_sample_id"]))
                        else:
                            print("\t".join(fields))

                        i += 1

def wrap_sequencing_emit(args, config, metadata={}, metrics={}):
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
    util.emit(config, ENDPOINTS["api.process.sequencing.add"], payload, quiet=args.quiet, sudo_as=args.sudo_as)

def wrap_library_emit(args, config, metadata={}, metrics={}):
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
                "library_protocol": args.apply_all_library[3],
                "library_primers": args.apply_all_library[4],
            })
        del v_args["apply_all_library"]
        del v_args["biosamples"]

    v_args["metadata"] = metadata
    v_args["biosamples"] = submit_biosamples
    util.emit(config, ENDPOINTS["api.artifact.library.add"], v_args, quiet=args.quiet, sudo_as=args.sudo_as)

def wrap_digitalresource_emit(args, config, metadata={}, metrics={}):
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

        #"pipe_id": args.pipeline[0],
        "pipe_hook": args.pipeline[0],
        "pipe_kind": args.pipeline[1],
        "pipe_name": args.pipeline[2],
        "pipe_version": args.pipeline[3],

        "publish_group": args.publish_group,
        "source_group": args.source_group,
        "source_artifact": args.source_artifact,
        "bridge_artifact": args.bridge_artifact,
        "artifact_uuid": args.artifact_uuid,
    }
    util.emit(config, ENDPOINTS["api.artifact.file.add"], payload, quiet=args.quiet, sudo_as=args.sudo_as)

def wrap_tag_emit(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]

    v_args["metadata"] = metadata
    util.emit(config, ENDPOINTS["api.meta.tag.add"], v_args, quiet=args.quiet, sudo_as=args.sudo_as)

def wrap_metric_emit(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]

    if v_args["artifact_path"]:
        v_args["artifact_path"] = os.path.abspath(v_args["artifact_path"])
    v_args["metrics"] = metadata
    del v_args["metadata"]
    util.emit(config, ENDPOINTS["api.meta.metric.add"], v_args, quiet=args.quiet, sudo_as=args.sudo_as)

def wrap_qc_emit(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]
    del v_args["metadata"]
    util.emit(config, ENDPOINTS["api.meta.qc.add"], v_args, quiet=args.quiet, sudo_as=args.sudo_as)

def wrap_publish_emit(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]
    v_args["metadata"] = metadata
    j = util.emit(config, ENDPOINTS["api.pag.accession.add"], v_args, quiet=args.quiet, sudo_as=args.sudo_as)
    if j["errors"] == 0:
        print(0, args.publish_group, j["updated"][0][2])
    else:
        print(1, args.publish_group, '-')

