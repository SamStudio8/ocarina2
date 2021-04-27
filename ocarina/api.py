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
