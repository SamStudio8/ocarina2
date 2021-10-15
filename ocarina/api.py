from . import util

class OcarinaAPI:
    def __init__(self, ocarina):
        self.ocarina = ocarina

    def response_to_user(self, j, return_payload):
        if j["errors"] == 0:
            status = True
        else:
            status = False

        return (status, return_payload)

    def get_task(self, task_id):
        payload = {
            "task_id": task_id,
        }
        endpoint = "api.majora.task.get"
        if self.ocarina.stream:
            endpoint = "api.majora.task.stream"
        j = util.emit(self.ocarina, self.endpoints[endpoint], payload, quiet=True)
        return self.response_to_user(j, j)

    def put_force_linked_biosample(self, central_sample_id, sender_sample_id):
        payload = {
            "biosamples": [
                {
                    "central_sample_id": central_sample_id,
                    "sender_sample_id": sender_sample_id,
                },
            ],
        }
        j = util.emit(self.ocarina, self.endpoints["api.artifact.biosample.addempty"], payload)
        return self.response_to_user(j, j)

    def put_library(self,
            library_name,
            biosamples,
            library_layout_config,
            library_seq_kit,
            library_seq_protocol,
            library_layout_insert_length=None,
            library_layout_read_length=None,
            metadata=None):

        #TODO Some sort of validation of Biosamples?
        if not metadata:
            metadata = {}
        payload = {
            "biosamples": biosamples,
            "library_layout_config": library_layout_config,
            "library_layout_insert_length": library_layout_insert_length,
            "library_layout_read_length": library_layout_read_length,
            "library_name": library_name,
            "library_seq_kit": library_seq_kit,
            "library_seq_protocol": library_seq_protocol,
            "metadata": metadata,
        }
        j = util.emit(self.ocarina, self.endpoints["api.artifact.library.add"], payload)
        return self.response_to_user(j, j)

    def put_sequencing(self,
                        run_name,
                        library_name,
                        instrument_make,
                        instrument_model,
                        bioinfo_pipe_name=None,
                        bioinfo_pipe_version=None,
                        end_time=None,
                        flowcell_id=None,
                        flowcell_type=None,
                        run_group=None,
                        sequencing_id=None,
                        start_time=None):

        payload = {
            "library_name": library_name,
            "run_group": run_group,
            "runs": [{
                "instrument_make": instrument_make,
                "instrument_model": instrument_model,
                "run_name": run_name,
                "bioinfo_pipe_name": bioinfo_pipe_name,
                "bioinfo_pipe_version": bioinfo_pipe_version,
                "end_time": end_time,
                "flowcell_id": flowcell_id,
                "flowcell_type": flowcell_type,
                "sequencing_id": sequencing_id,
                "start_time": start_time,
            }],
        }
        j = util.emit(self.ocarina, self.endpoints["api.process.sequencing.add"], payload)
        return self.response_to_user(j, j)



    def put_accession(self, publish_group, service, accession, contains=False, accession2=None, accession3=None, public=False, public_date=None, submitted=False):
        payload = {
            "publish_group": publish_group,
            "contains": contains,
            "service": service,
            "accession": accession,
            "accession2": accession2,
            "accession3": accession3,
            "public": public,
            "public_date": public_date,
            "submitted": submitted,

        }
        j = util.emit(self.ocarina, self.endpoints["api.pag.accession.add"], payload)
        if j["errors"] == 0:
            updated_pag = j["updated"][0][2] # gross
        else:
            updated_pag = None

        return self.response_to_user(j, {
            "publish_group": updated_pag,
        })

    def get_artifact_info(self, query):
        payload = {
            "params": {
                "q": query,
            }
        }
        j = util.emit(self.ocarina, self.endpoints["api.v0.artifact.info"], payload)
        return self.response_to_user(j, j["info"])
