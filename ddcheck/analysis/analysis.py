from ddcheck.analysis.top import analyse_top_output
from ddcheck.storage import AnalysisState, DdcheckMetadata
from ddcheck.storage.upload import write_metadata_to_disk


def analyse_tarball(metadata: DdcheckMetadata, node: str) -> AnalysisState:
    try:
        top_result = analyse_top_output(metadata, node)

        return top_result
    finally:
        write_metadata_to_disk(metadata)
