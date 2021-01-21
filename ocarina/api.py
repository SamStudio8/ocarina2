from . import util

class OcarinaAPI:
    def __init__(self, ocarina):
        self.ocarina = ocarina

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
        j = util.emit(self.ocarina, self.endpoints["api.pag.accession.add"], payload, interactive=False)
        if j["errors"] == 0:
            status = True
            updated_pag = j["updated"][0][2] # gross
        else:
            status = False
            updated_pag = None

        return (status, {
            "publish_group": updated_pag,
        })
