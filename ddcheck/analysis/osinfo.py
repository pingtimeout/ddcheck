from ddcheck.storage import AnalysisState, DdcheckMetadata


def analyse_os_info(metadata: DdcheckMetadata, node: str) -> AnalysisState:
    return AnalysisState.NOT_STARTED
