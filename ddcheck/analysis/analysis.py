from ddcheck.analysis.osinfo import analyse_os_info
from ddcheck.analysis.top import analyse_top_output
from ddcheck.storage import AnalysisState, DdcheckMetadata
from ddcheck.storage.upload import write_metadata_to_disk


def analyse_tarball(metadata: DdcheckMetadata, node: str) -> AnalysisState:
    try:
        top_result = analyse_top_output(metadata, node)
        os_info_result = analyse_os_info(metadata, node)
        return top_result.max(os_info_result)
    finally:
        write_metadata_to_disk(metadata)
