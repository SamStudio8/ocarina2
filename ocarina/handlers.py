from subprocess import check_output
import os
import sys

class FiletypeHandler(object):
    def __init__(self, path):
        self.path = path
        self.metadata = {}

    def check_integrity(self):
        return {}

    def make_metadata(self):
        return {}


class BamFileHandler(FiletypeHandler):
    def check_integrity(self):

        self.alignments = -1
        has_index = None
        has_indate_index = None

        try:
            p = check_output("samtools view -c -F4 %s" % self.path, shell=True)
            self.alignments = int(p.split("\n")[0].strip())
        except Exception as e:
            pass

        if os.path.exists(self.path + ".bai"):
            has_index = True
        else:
            has_index = False

        if has_index:
            if os.path.getmtime(self.path) <= os.path.getmtime(self.path + ".bai"):
                has_indate_index = True
            else:
                has_indate_index = False

        return {
            "has_reads": {"msg": "has no mapped reads", "result": self.alignments == 0},
            "has_index": {"msg": "has no index", "result": not has_index},
            "has_outed_index": {"msg": "has an index older than itself", "result": not has_indate_index},
        }

    def make_metadata(self):
        metadata = {}
        if self.alignments > -1:
            metadata["n_alignments"] = self.alignments
        return metadata


class FastaFileHandler(FiletypeHandler):

    def check_integrity(self):
        from .handler_utils import readfq

        self.seqs = 0
        self.size = os.path.getsize(self.path)
        self.has_headspace = False
        self.has_noncharseq = False

        heng_iter = readfq(open(self.path))
        for name, seq, qual in heng_iter:
            if " " in name: # i stopped heng's code partitioning on space
                self.has_headspace = True

            self.seqs += 1

            # too slow for real uses but will work in viral consortium stuff for now
            if 'X' in seq or '-' in seq or ' ' in seq:
                self.has_noncharseq = True

        return {
            "isnot_empty": {"msg": "is empty", "result": self.size == 0},
            "hasspace_head": {"msg": "has at least one sequence with a space in the header", "result": self.has_headspace},
            "hasnonchar_seqs": {"msg": "has at least one sequence containing a space, X or -", "result": self.has_noncharseq},
            "has_seq": {"msg": "has no sequence headers", "result": self.seqs == 0},
        }

    def make_metadata(self):
        metadata = {}
        if self.seqs > -1:
            metadata["n_sequences"] = self.seqs
        return metadata
