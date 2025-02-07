import logging
import re
from glob import glob
from pathlib import Path

from ddcheck.storage import AnalysisState, DdcheckMetadata, Source

logger = logging.getLogger(__name__)


def _parse_online_cpus(online_cpus_str: str) -> list[int]:
    """Parse a CPU range string like '0-15' into a list of integers."""
    result: list[int] = []
    for part in online_cpus_str.split(","):
        if "-" in part:
            start, end = map(int, part.split("-"))
            result.extend(range(start, end + 1))
        else:
            result.append(int(part))
    return sorted(result)


def analyse_os_info(metadata: DdcheckMetadata, node: str) -> AnalysisState:
    # Initialize new fields if they don't exist
    metadata.total_memory_kb.setdefault(node, 0)
    metadata.total_cpus.setdefault(node, 0)
    metadata.online_cpus.setdefault(node, [])

    # If node does not exist in metadata, log an error and mark it as skipped
    if node not in metadata.nodes:
        logger.error(f"Node {node} not found in metadata nodes: {metadata.nodes}")
        metadata.analysis_state[node][Source.OS_INFO] = AnalysisState.SKIPPED
        return AnalysisState.SKIPPED

    # Skip if already analyzed
    current_state = metadata.analysis_state.get(node, {}).get(
        Source.OS_INFO, AnalysisState.NOT_STARTED
    )
    if current_state != AnalysisState.NOT_STARTED:
        logger.debug(f"Skipping analysis for node {node} - state is {current_state}")
        return current_state

    metadata.analysis_state[node][Source.OS_INFO] = AnalysisState.IN_PROGRESS

    # Find os_info.txt file for node
    extract_path = Path(metadata.extract_path)
    pattern = str(extract_path / "*" / "node-info" / node / "os_info.txt")
    matching_files = glob(pattern)

    if not matching_files:
        logger.error(f"Could not find os_info.txt file for node {node} in {pattern}")
        metadata.analysis_state[node][Source.OS_INFO] = AnalysisState.SKIPPED
        return metadata.analysis_state[node][Source.OS_INFO]

    os_info_file = Path(matching_files[0])
    if not os_info_file.is_file():
        logger.error(f"Found path is not a file: {os_info_file}")
        metadata.analysis_state[node][Source.OS_INFO] = AnalysisState.SKIPPED
        return metadata.analysis_state[node][Source.OS_INFO]

    try:
        with open(os_info_file) as f:
            content = f.read()

            # Parse total memory
            mem_match = re.search(r"MemTotal:\s+(\d+)\s*kB", content)
            if mem_match:
                metadata.total_memory_kb[node] = int(mem_match.group(1))

            # Parse total CPUs
            cpu_match = re.search(r"CPU\(s\):\s+(\d+)", content)
            if cpu_match:
                metadata.total_cpus[node] = int(cpu_match.group(1))

            # Parse online CPUs
            online_match = re.search(r"On-line CPU\(s\) list:\s+([0-9,-]+)", content)
            if online_match:
                metadata.online_cpus[node] = _parse_online_cpus(online_match.group(1))

            # Verify CPU counts match
            if metadata.total_cpus[node] != len(metadata.online_cpus[node]):
                logger.warning(
                    f"Node {node} has {metadata.total_cpus[node]} total CPUs but "
                    f"{len(metadata.online_cpus[node])} online CPUs"
                )

            metadata.analysis_state[node][Source.OS_INFO] = AnalysisState.COMPLETED

    except Exception as e:
        logger.error(f"Error reading os_info file {os_info_file}: {e}")
        metadata.analysis_state[node][Source.OS_INFO] = AnalysisState.FAILED

    return metadata.analysis_state[node][Source.OS_INFO]
