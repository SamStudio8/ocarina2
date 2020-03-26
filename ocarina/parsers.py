from . import handlers

filetype_handlers = {
    "fasta":    ( ["fa", "fas", "fasta", "fa.gz"], handlers.FastaFileHandler ),
    "bam":      ( ["bam"], handlers.BamFileHandler ),
}

def get_parser_for_type(path):
    target = path.lower()
    for handler in filetype_handlers:
        for extension in filetype_handlers[handler][0]:
            if target.endswith(extension):
                return filetype_handlers[handler][1](path)
    return None

