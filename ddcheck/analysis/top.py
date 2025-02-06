import logging
from glob import glob
from pathlib import Path
from typing import Dict, List

from ddcheck.storage import DdcheckMetadata
from ddcheck.storage.upload import write_metadata_to_disk

logger = logging.getLogger(__name__)


def parse_cpu_line(cpu_data: Dict[str, List[float]], line: str) -> bool:
    """
    Parse a line containing CPU data and update the cpu_data dictionary.

    :param cpu_data: Dictionary to update with CPU measurements
    :param line: Line to parse
    :return: True if the line was parsed as CPU data, False otherwise
    """
    if not line.startswith("%Cpu(s):"):
        return False

    # Remove "%Cpu(s):" prefix and split by comma
    cpu_parts = line.replace("%Cpu(s):", "").strip().split(",")

    # Process each CPU measurement
    for part in cpu_parts:
        value_str, key = part.strip().split()
        cpu_data[key].append(float(value_str))

    return True


def analyse_top_output(metadata: DdcheckMetadata, node: str) -> str:
    try:
        return _analyse_top_output(metadata, node)
    finally:
        write_metadata_to_disk(metadata)


def _analyse_top_output(metadata: DdcheckMetadata, node: str) -> str:
    # If node does not exist in metadata, log an error and mark it as skipped
    if node not in metadata.nodes:
        logger.error(f"Node {node} not found in metadata nodes: {metadata.nodes}")
        metadata.analysis_state[node] = "skipped"

    # Skip the analysis if it has already been attempted
    current_state = metadata.analysis_state.get(node, "not_started")
    if current_state != "not_started":
        logger.debug(f"Skipping analysis for node {node} - state is {current_state}")
        return current_state

    # Mark analysis as in progress
    metadata.analysis_state[node] = "in_progress"

    # Find ttop directory for node
    extract_path = Path(metadata.extract_path)
    pattern = str(extract_path / "*" / "ttop" / node / "ttop.txt")
    matching_files = glob(pattern)

    if not matching_files:
        logger.error(f"Could not find ttop.txt file for node {node} in {pattern}")
        metadata.analysis_state[node] = "skipped"
        return metadata.analysis_state[node]

    ttop_file = Path(matching_files[0])
    if not ttop_file.is_file():
        logger.error(f"Found path is not a file: {ttop_file}")
        metadata.analysis_state[node] = "skipped"
        return metadata.analysis_state[node]

    # Initialize CPU data collections
    cpu_data: Dict[str, List[float]] = {
        "us": [],
        "sy": [],
        "ni": [],
        "id": [],
        "wa": [],
        "hi": [],
        "si": [],
        "st": [],
    }

    try:
        with open(ttop_file) as f:
            for line in f:
                parse_cpu_line(cpu_data, line)
            metadata.cpu_usage[node] = cpu_data
            metadata.analysis_state[node] = "completed"
    except Exception as e:
        logger.error(f"Error reading ttop file {ttop_file}: {e}")
        metadata.analysis_state[node] = "failed"

    return metadata.analysis_state[node]
