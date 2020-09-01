import re
import os
import sys
import csv

import json
import time
from . import util
from . import parsers
from .version import __version__

import argparse
import datetime

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

        "api.artifact.biosample.query.validity": "/api/v2/artifact/biosample/query/validity/",

        "api.majora.summary.get": "/api/v2/majora/summary/get/",
        "api.outbound.summary.get": "/api/v2/outbound/summary/get/",
        "api.majora.task.get": "/api/v2/majora/task/get/",

        "api.majora.task.delete": "/api/v2/majora/task/delete/",

        "api.group.mag.get": "/api/v2/group/mag/get/",
}


def cli():

    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--quiet", help="suppress the large welcoming ocarina", action="store_true")
    parser.add_argument("--env", help="use env vars instead of ~/.ocarina", action="store_true")
    parser.add_argument("--angry", help="exit if API returns errors > 0", action="store_true", default=False)
    parser.add_argument("-v", "--version", action='version', version="ocarina v%s" %  __version__)
    parser.add_argument("--oauth", help="use experimental OAuth authorization", action="store_true", default=False)

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
    biosample_parser.add_argument("--is-surveillance", action="store_true")

    bsp_date = biosample_parser.add_mutually_exclusive_group(required=True)
    bsp_date.add_argument("--collection-date")
    bsp_date.add_argument("--received-date")

    biosample_parser.add_argument("--source-age")
    biosample_parser.add_argument("--source-sex")
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
    publish_parser.add_argument("--accession", required=False)
    publish_parser.add_argument("--accession2", required=False)
    publish_parser.add_argument("--accession3", required=False)
    publish_parser.add_argument("--public", action="store_true")
    publish_parser.add_argument("--public-date", type=lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').strftime('%Y-%m-%d'))
    publish_parser.add_argument("--submitted", action="store_true")
    #publish_parser.add_argument("--rejected-reason", required=False)
    publish_parser.set_defaults(func=wrap_publish_emit)


    list_parser = action_parser.add_parser("list")
    list_parser.add_argument("path", help="node://absolute/path/to/artifact/or/group")
    list_parser.add_argument("--sep", default="/", required=False)
    list_parser.add_argument("--force", "-F", action="store_true")
    list_parser.set_defaults(func=wrap_list_mag)


    get_parser = action_parser.add_parser("get")
    get_parser.add_argument("--task-wait-attempts", help="Number of attempts to query a task from the task endpoint [10]", type=int, default=10)
    get_parser.add_argument("--task-wait-minutes", help="Number of minutes to wait between task fetching attempts [1]", type=int, default=1)
    get_parser.add_argument("--task-wait", help="Patiently wait for the result from the Majora task endpoint", action="store_true")
    get_parser.add_argument("--task-id", help="Request the result from the Majora task endpoint")
    get_parser.add_argument("--task-del", help="Destroy the task result if this command finishes successfully", action="store_true")
    get_subparsers = get_parser.add_subparsers(title="actions")

    get_biosample_parser = get_subparsers.add_parser("biosample", parents=[get_parser], add_help=False,
            help="fetch a biosample")
    get_biosample_parser.add_argument("--central-sample-id", "--coguk-sample-id", required=True)
    get_biosample_parser.set_defaults(func=wrap_get_biosample)

    get_biosamplev_parser = get_subparsers.add_parser("biosample-validity", parents=[get_parser], add_help=False,
            help="fetch biosamples status")
    get_biosamplev_parser.add_argument("--biosamples", nargs='+', required=True)
    get_biosamplev_parser.add_argument("--tsv", action="store_true")
    get_biosamplev_parser.set_defaults(func=wrap_get_biosamplev)

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

    get_pag_parser.add_argument("--service-name")
    get_pag_parser.add_argument("--public", action="store_true")
    get_pag_parser.add_argument("--private", action="store_true")

    get_pag_parser.add_argument("--published-after", type=lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').strftime('%Y-%m-%d'))

    get_pag_parser.add_argument("--ls-files", action="store_true")
    get_pag_parser.add_argument("--ofield", nargs=3, metavar=("field", "as", "default"), action="append")
    get_pag_parser.add_argument("--odelimiter", default='\t')
    get_pag_parser.add_argument("--ffield-true", nargs=1, metavar=("field",), action="append")
    get_pag_parser.set_defaults(func=wrap_get_qc)


    get_summary_parser = get_subparsers.add_parser("summary", parents=[get_parser], add_help=False,
            help="Get summary metrics")
    get_summary_parser.add_argument("--gte-date")
    get_summary_parser.add_argument("--md", action="store_true")
    get_summary_parser.set_defaults(func=wrap_get_summary)

    get_osummary_parser = get_subparsers.add_parser("outbound-summary", parents=[get_parser], add_help=False,
            help="Get outbound summary metrics")
    get_osummary_parser.add_argument("--service", required=True)
    get_osummary_parser.add_argument("--user", required=False)
    get_osummary_parser.add_argument("--gte-date", required=True)
    get_osummary_parser.add_argument("--md", action="store_true")
    get_osummary_parser.add_argument("--md-from-wave", type=int, default=1)
    get_osummary_parser.add_argument("--md-skip-zero", action="store_true")
    get_osummary_parser.set_defaults(func=wrap_get_outbound_summary)

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
    util.emit(config, ENDPOINTS["api.artifact.biosample.add"], payload, quiet=args.quiet, sudo_as=args.sudo_as, oauth=args.oauth)

def wrap_get_biosamplev(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]
    j = util.emit(config, ENDPOINTS["api.artifact.biosample.query.validity"], v_args, quiet=args.quiet, oauth=args.oauth)

    if args.tsv:
        if len(j["result"]) > 0:
            print("sample_id\texists\thas_metadata")
            for sample_id, sample_d in j["result"].items():
                print("\t".join([str(x) for x in [
                    sample_id,
                    1 if sample_d["exists"] else 0,
                    1 if sample_d["has_metadata"] else 0,
                ]]))

def wrap_get_biosample(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]
    util.emit(config, ENDPOINTS["api.artifact.biosample.get"], v_args, quiet=args.quiet, oauth=args.oauth)

def wrap_get_outbound_summary(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]
    j = util.emit(config, ENDPOINTS["api.outbound.summary.get"], v_args, quiet=args.quiet, oauth=args.oauth)

    if args.md:
        cumsum = 0
        if len(j["get"]["intervals"]) >= 1:
            print("| Wave | Date | Sites | Submitted | Rejected | Released | Cumulative released |")
            print("|:-----|:-----|------:|----------:|---------:|---------:|--------------------:|")
            non_zero_i = 0
            for i, interval in enumerate(j["get"]["intervals"]):
                mod = '~' if not interval["whole"] else ''
                cumsum += int(interval["released"])

                c = i
                if args.md_skip_zero:
                    c = non_zero_i
                    if int(interval["released"]) == 0 and int(interval["submitted"]) == 0:
                        continue
                    else:
                        non_zero_i += 1

                print ("| %s | %s | %d | %d | %d | %d | %d" % (
                    "%s%d" % (mod, args.md_from_wave + c),
                    interval["dt"],
                    0,
                    interval["submitted"],
                    interval["rejected"],
                    interval["released"],
                    cumsum,
                ))


def wrap_get_summary(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]
    j = util.emit(config, ENDPOINTS["api.majora.summary.get"], v_args, quiet=args.quiet, oauth=args.oauth)

    if args.md:
        if len(j["get"]["site_qc"]) >= 1:
            print("| Sample Site | Seq Site | Count | Pass | Pass% | Fail | Fail% | Surveillance | Surveillance% |")
            print("|------------:|---------:|------:|-----:|------:|-----:|------:|-------------:|--------------:|")
            for group in j["get"]["site_qc"]:
                print("| %s | %s | %d | %d | %.2f | %d | %.2f | %d | %.2f |" % (
                    group["sourcesite"] if group["sourcesite"] != group["site"] else "-",
                    group["site"],
                    group["count"],
                    group["pass_count"],
                    group["pass_count"]/group["count"] * 100,
                    group["fail_count"],
                    group["fail_count"]/group["count"] * 100,
                    group["surveillance_num"],
                    0 if group["surveillance_dom"] == 0 else group["surveillance_num"]/group["surveillance_dom"] * 100,
                ))

def wrap_get_task(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]
    j = util.emit(config, ENDPOINTS["api.majora.task.get"], v_args, quiet=args.quiet, oauth=args.oauth)

def wrap_del_task(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]
    j = util.emit(config, ENDPOINTS["api.majora.task.delete"], v_args, quiet=args.quiet, oauth=args.oauth)

def wrap_get_qc(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]

    if args.task_id:
        j = util.emit(config, ENDPOINTS["api.majora.task.get"], v_args, quiet=args.quiet, oauth=args.oauth)
        #TODO move this to part of emit
        if j.get("task", {}).get("state", "") != "SUCCESS":
            return
    else:
        j = util.emit(config, ENDPOINTS["api.pag.qc.get"], v_args, quiet=args.quiet, oauth=args.oauth)

    #TODO sam why
    if args.task_wait:
        if not v_args["task_id"]:
            try:
                task_id = j.get("tasks", [None])[0]
            except:
                sys.exit(2)
            v_args["task_id"] = task_id
        state = "PENDING"
        attempt = 0
        while state == "PENDING" and attempt < args.task_wait_attempts:
            attempt += 1
            sys.stderr.write("[WAIT] Giving Majora a minute to finish task %s (%d)...\n" % (v_args["task_id"], attempt))
            time.sleep(60 * args.task_wait_minutes)
            j = util.emit(config, ENDPOINTS["api.majora.task.get"], v_args, quiet=True, oauth=args.oauth)
            state = j.get("task", {}).get("state", "UNKNOWN")
        sys.stderr.write("[WAIT] Finished waiting with status %s (%d)...\n" % (state, attempt))

    if args.ls_files:
        if "get" not in j or "count" not in j["get"]:
            sys.exit(2)
        if j["get"]["count"] >= 1:
            for pag in j["get"]["result"]:
                pag_is_pass = pag["is_pass"]
                pag = pag["pag"]
                if "Digital Resource" in pag["artifacts"]:
                    for dra in pag["artifacts"]["Digital Resource"]:
                        sys.stdout.write("\t".join([
                            pag["published_name"],
                            dra["current_kind"],
                            dra["current_path"],
                            dra.get("current_hash", "0"),
                            str(dra.get("current_size", 0)),
                            "PASS" if pag_is_pass else "FAIL",
                        ]) + '\n')
    elif args.ofield:
        csv_w = csv.DictWriter(sys.stdout, fieldnames=[f[1] for f in args.ofield], delimiter=args.odelimiter)
        csv_w.writeheader()
        skipped = 0
        if "get" not in j or "count" not in j["get"]:
            sys.exit(2)
        if j["get"]["count"] >= 1:
            for pag in j["get"]["result"]:
                # Flatten the PAG to unique distinguished objects
                pag = pag["pag"]
                include = True
                if args.ffield_true:
                    for field in args.ffield_true:
                        if field[0] in pag:
                            if not pag[field[0]]:
                                include = False
                        else:
                            pass
                if not include:
                    skipped += 1
                    continue

                metadata = {k:v for k,v in pag.items() if type(v) != dict and type(v) != list}
                if "accessions" in pag:
                    for service in pag["accessions"]:
                        for mkey, mvalue in pag["accessions"][service].items():
                            if mkey == "service":
                                continue
                            mkey = "accession.%s.%s" % (service.lower(), mkey)
                            metadata[mkey] = mvalue
                if "qc_reports" in pag:
                    for report in pag["qc_reports"]:
                        metadata["qc.%s" % report["test_name"]] = True if report["is_pass"]=="True" else False

                for artifact_g in pag["artifacts"]:
                    for artifact in pag["artifacts"][artifact_g]:
                        current_kind = artifact.get("current_kind", "") # TODO euch
                        for k, v in artifact.items():

                            if k == "metadata":
                                for namespace in artifact["metadata"]:
                                    for mkey, mvalue in artifact["metadata"][namespace].items():
                                        mkey = "%s.%s" % (namespace, mkey)
                                        if mkey not in metadata:
                                            metadata[mkey] = mvalue
                                        else:
                                            del metadata[mkey]
                            elif k == "metrics":
                                for namespace in artifact["metrics"]:
                                    for mkey, mvalue in artifact["metrics"][namespace].items():
                                        if mkey == "records":
                                            for record_i, record in enumerate(mvalue):
                                                for sub_name, sub_value in record.items():
                                                    skey = "metric.%s.%d.%s" % (namespace, record_i+1, sub_name)
                                                    metadata[skey] = sub_value
                                        else:
                                            mkey = "metric.%s.%s" % (namespace, mkey)

                                        if mkey not in metadata:
                                            metadata[mkey] = mvalue
                                        else:
                                            del metadata[mkey]
                            elif k.startswith("supplement_"):
                                for mkey, mvalue in artifact[k].items():
                                    mkey = "supplement.%s.%s" % (k.split('_')[1], mkey)
                                    if mkey not in metadata:
                                        metadata[mkey] = mvalue
                                    else:
                                        del metadata[mkey]
                            else:
                                if current_kind:
                                    k = "%s.%s" % (current_kind, k)
                                if k not in metadata and type(v) != dict and type(v) != list:
                                    metadata[k] = v
                                elif k in metadata:
                                    del metadata[k] # unique stuff only for now


                row = {}
                for ofield in args.ofield:
                    field, as_, default = ofield
                    if field[0] == '~':
                        v = field[1:]
                        for m in re.findall("{\w+}", field):
                            if m[1:-1] in metadata:
                                v = v.replace(m, metadata[m[1:-1]])
                    #elif fields[0] == ':'
                    #    v = field[1:]
                    #    for vs in [re.findall(v, k) for k in metadata]:
                    #        pass
                    elif field in metadata and metadata[field] is not None:
                        v = metadata[field]
                    else:
                        v = default
                    row[as_] = v
                csv_w.writerow(row)
        sys.stderr.write("Skipped %d\n" % skipped)
                

    if args.task_del and j.get("task", {}).get("state", "") == "SUCCESS":
        j = util.emit(config, ENDPOINTS["api.majora.task.delete"], v_args, quiet=args.quiet, oauth=args.oauth)

def wrap_get_sequencing(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]

    if args.task_id:
        j = util.emit(config, ENDPOINTS["api.majora.task.get"], v_args, quiet=args.quiet, oauth=args.oauth)
        #TODO move this to part of emit
        if j.get("task", {}).get("state", "") != "SUCCESS":
            return
    else:
        j = util.emit(config, ENDPOINTS["api.process.sequencing.get"], v_args, quiet=args.quiet, oauth=args.oauth)

    #TODO sam why
    if args.task_wait:
        if not v_args["task_id"]:
            try:
                task_id = j.get("tasks", [None])[0]
            except:
                sys.exit(2)
            v_args["task_id"] = task_id
        state = "PENDING"
        attempt = 0
        while state == "PENDING" and attempt < args.task_wait_attempts:
            attempt += 1
            sys.stderr.write("[WAIT] Giving Majora a minute to finish task %s (%d)...\n" % (v_args["task_id"], attempt))
            time.sleep(60 * args.task_wait_minutes)
            j = util.emit(config, ENDPOINTS["api.majora.task.get"], v_args, quiet=True, oauth=args.oauth)
            state = j.get("task", {}).get("state", "UNKNOWN")
        sys.stderr.write("[WAIT] Finished waiting with status %s (%d)...\n" % (state, attempt))

    if "get" not in j or "count" not in j["get"]:
        sys.exit(2)
    elif j["get"]["count"] == 0:
        sys.exit(3)
    if j["get"]["count"] >= 1 and v_args["tsv"]:
        i = 0
        header = None

        if len(j["get"]["result"]) >= 1:
            all_possible_meta_keys = set([])
            for run in j["get"]["result"]:
                for l in j["get"]["result"][run]["libraries"]:
                    if l["metadata"]:
                        flat_meta = {}
                        for tag in l["metadata"]:
                            for name in l["metadata"][tag]:
                                flat_meta["meta.%s.%s" % (tag, name)] = l["metadata"][tag][name]
                                all_possible_meta_keys.add("meta.%s.%s" % (tag, name))
                        l.update(flat_meta)
                    for b in l["biosamples"]:
                        if b["metadata"]:
                            flat_meta = {}
                            for tag in b["metadata"]:
                                for name in b["metadata"][tag]:
                                    flat_meta["meta.%s.%s" % (tag, name)] = b["metadata"][tag][name]
                                    all_possible_meta_keys.add("meta.%s.%s" % (tag, name))
                            b.update(flat_meta)
                        try:
                            del b["metadata"]
                        except:
                            pass

                        if b["metrics"]:
                            flat_meta = {}
                            for tag in b["metrics"]:
                                for name in b["metrics"][tag]:
                                    if name == "records":
                                        for record_i, record in enumerate(b["metrics"][tag][name]):
                                            for sub_name, sub_value in record.items():
                                                flat_meta["metric.%s.%d.%s" % (tag, record_i+1, sub_name)] = sub_value
                                                all_possible_meta_keys.add("metric.%s.%d.%s" % (tag, record_i+1, sub_name))
                                    else:
                                        flat_meta["metric.%s.%s" % (tag, name)] = b["metrics"][tag][name]
                                        all_possible_meta_keys.add("metric.%s.%s" % (tag, name))
                            b.update(flat_meta)
                        try:
                            del b["metrics"]
                        except:
                            pass
                    try:
                        del l["metadata"]
                    except:
                        pass

            for run in j["get"]["result"]:
                row_master = j["get"]["result"][run]
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
    util.emit(config, ENDPOINTS["api.process.sequencing.add"], payload, quiet=args.quiet, sudo_as=args.sudo_as, oauth=args.oauth)

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
    util.emit(config, ENDPOINTS["api.artifact.library.add"], v_args, quiet=args.quiet, sudo_as=args.sudo_as, oauth=args.oauth)

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
    util.emit(config, ENDPOINTS["api.artifact.file.add"], payload, quiet=args.quiet, sudo_as=args.sudo_as, oauth=args.oauth)

def wrap_tag_emit(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]

    v_args["metadata"] = metadata
    util.emit(config, ENDPOINTS["api.meta.tag.add"], v_args, quiet=args.quiet, sudo_as=args.sudo_as, oauth=args.oauth)

def wrap_metric_emit(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]

    if v_args["artifact_path"]:
        v_args["artifact_path"] = os.path.abspath(v_args["artifact_path"])
    v_args["metrics"] = metadata
    del v_args["metadata"]
    util.emit(config, ENDPOINTS["api.meta.metric.add"], v_args, quiet=args.quiet, sudo_as=args.sudo_as, oauth=args.oauth)

def wrap_qc_emit(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]
    del v_args["metadata"]
    util.emit(config, ENDPOINTS["api.meta.qc.add"], v_args, quiet=args.quiet, sudo_as=args.sudo_as, oauth=args.oauth)

def wrap_list_mag(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]
    j = util.emit(config, ENDPOINTS["api.group.mag.get"], v_args, quiet=True, sudo_as=None, oauth=args.oauth)

    ec = j.get("error_code", "")
    if ec.startswith("BIGMAG"):
        print("MAG contains %s groups or artifacts, if you are sure you want to list it use --force." % ec.split(':')[1])
        return

    if j.get("mag"):
        from tabulate import tabulate
        from colorama import init
        init()

        from colorama import Fore, Back, Style

        table = []
        row = []
        row.append(Fore.YELLOW + '...' + Style.RESET_ALL)
        if j["mag"]["root_group"]:
            row.append(Fore.YELLOW + j["mag"]["root_group"]["name"] + Style.RESET_ALL)
            row.append(None)
            row.append(j["mag"]["root_group"]["group_kind"])
            row.append(j["mag"]["root_group"]["group_path"])
            row.append(Fore.YELLOW + j["mag"]["root_group"]["id"] + Style.RESET_ALL)
        else:
            row.append(None)
            row.append(None)
            row.append(None)
            row.append(None)
            row.append(None)
        table.append(row)

        row = []
        row.append(Fore.YELLOW + '.. ' + Style.RESET_ALL)
        if j["mag"]["parent_group"]:
            row.append(Fore.YELLOW + j["mag"]["parent_group"]["name"] + Style.RESET_ALL)
            row.append(None)
            row.append(j["mag"]["parent_group"]["group_kind"])
            row.append(j["mag"]["parent_group"]["group_path"])
            row.append(Fore.YELLOW + j["mag"]["parent_group"]["id"] + Style.RESET_ALL)
        else:
            row.append(None)
            row.append(None)
            row.append(None)
            row.append(None)
            row.append(None)
        table.append(row)

        row = []
        row.append(Fore.YELLOW + '.  ' + Style.RESET_ALL)
        row.append(Fore.YELLOW + j["mag"]["name"] + Style.RESET_ALL)
        row.append(None)
        row.append(j["mag"]["group_kind"])
        row.append(j["mag"]["group_path"])
        row.append(Fore.YELLOW + j["mag"]["id"] + Style.RESET_ALL)
        table.append(row)

        row = []
        row.append(None)
        row.append(None)
        row.append(None)
        row.append(None)
        row.append(None)
        row.append(None)
        table.append(row)

        for g_tc, g_t in [("gc", "children"), ("gl", "hlinks"), ("sl", "slinks")]:
            for g in j["mag"][g_t]:
                row = []
                if g_tc == "sl":
                    if g["to_group"]:
                        row.append(Fore.CYAN + '%s-' % g_tc + Style.RESET_ALL)
                        row.append(Fore.CYAN + g["name"] + Style.RESET_ALL)
                        row.append(g["to_group"]["group_path"])
                        row.append(g["to_group"]["name"])
                        row.append(j["mag"]["group_path"])
                        row.append(Fore.CYAN + g["to_group"]["id"] + Style.RESET_ALL)
                    else:
                        row.append(Fore.RED + Back.BLACK + '%s-' % g_tc + Style.RESET_ALL)
                        row.append(Fore.RED + Back.BLACK + g["name"] + Style.RESET_ALL)
                        row.append(None)
                        row.append(None)
                        row.append(j["mag"]["group_path"])
                        row.append(Fore.RED + Back.BLACK + j["mag"]["id"] + Style.RESET_ALL)
                    table.append(row)
                else:
                    row.append(Fore.BLUE + '%s-' % g_tc + Style.RESET_ALL)
                    row.append(Fore.BLUE + g['name'] + Style.RESET_ALL)
                    row.append(None)
                    row.append(g['group_kind'])
                    row.append(g['group_path'])
                    row.append(Fore.BLUE + g['id'] + Style.RESET_ALL)
                    table.append(row)
                    for a in g.get('artifacts', []):
                        row = []
                        row.append(Fore.WHITE + '-%sa' % g_tc[1] + Style.RESET_ALL)
                        row.append(a['name'])
                        row.append(a['path'])
                        row.append(a['kind'])
                        row.append(g['name'])
                        row.append(a['id'])
                        table.append(row)
                    row = [None]*6
                    table.append(row)
        print(tabulate(table, tablefmt='simple', headers=[
            "",
            "ANAME",
            "APATH",
            "ATYPE",
            "GROUP",
            "MAJORA UUID",
        ]))


def wrap_publish_emit(args, config, metadata={}, metrics={}):
    v_args = vars(args)
    del v_args["func"]
    v_args["metadata"] = metadata
    #v_args["rejected"] = False
    #if v_args["rejected_reason"]:
    #    v_args["rejected"] = True
    j = util.emit(config, ENDPOINTS["api.pag.accession.add"], v_args, quiet=args.quiet, sudo_as=args.sudo_as, oauth=args.oauth)
    if j["errors"] == 0:
        print(0, args.publish_group, j["updated"][0][2])
    else:
        print(1, args.publish_group, '-')

