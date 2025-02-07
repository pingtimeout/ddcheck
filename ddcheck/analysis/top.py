import logging
from datetime import datetime
from glob import glob
from pathlib import Path
from typing import Dict, List

from ddcheck.storage import AnalysisState, DdcheckMetadata
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


def _maybe_parse_time_and_load_average_line(
    time_data: list[datetime],
    load_1min: list[float],
    load_5min: list[float],
    load_15min: list[float],
    line: str,
) -> bool:
    """
    Parse a line containing time and load average data and update the respective lists.

    :param time_data: List to append datetime values to
    :param load_1min: List to append 1-minute load averages to
    :param load_5min: List to append 5-minute load averages to
    :param load_15min: List to append 15-minute load averages to
    :param line: Line to parse
    :return: True if the line was parsed as time/load data, False otherwise
    """
    if not line.startswith("top - "):
        return False

    # Extract time and load average parts
    parts = line.split(",  load average: ")
    if len(parts) != 2:
        return False

    # Extract and parse time
    time_str = parts[0].split()[2]  # "top - 15:06:43" -> "15:06:43"
    try:
        time_obj = datetime.strptime(time_str, "%H:%M:%S")
        time_data.append(time_obj)
    except ValueError:
        return False

    # Extract load averages
    load_strs = parts[1].strip().split(", ")
    if len(load_strs) != 3:
        return False

    try:
        load_1min.append(float(load_strs[0]))
        load_5min.append(float(load_strs[1]))
        load_15min.append(float(load_strs[2]))
    except ValueError:
        return False

    return True


def analyse_top_output(metadata: DdcheckMetadata, node: str) -> AnalysisState:
    try:
        return _analyse_top_output(metadata, node)
    finally:
        write_metadata_to_disk(metadata)


def _analyse_top_output(metadata: DdcheckMetadata, node: str) -> AnalysisState:
    # If node does not exist in metadata, log an error and mark it as skipped
    if node not in metadata.nodes:
        logger.error(f"Node {node} not found in metadata nodes: {metadata.nodes}")
        metadata.analysis_state[node] = AnalysisState.SKIPPED

    # Skip the analysis if it has already been attempted
    current_state = metadata.analysis_state.get(node, AnalysisState.NOT_STARTED)
    if current_state != AnalysisState.NOT_STARTED:
        logger.debug(f"Skipping analysis for node {node} - state is {current_state}")
        return current_state

    # Mark analysis as in progress
    metadata.analysis_state[node] = AnalysisState.IN_PROGRESS

    # Find ttop directory for node
    extract_path = Path(metadata.extract_path)
    pattern = str(extract_path / "*" / "ttop" / node / "ttop.txt")
    matching_files = glob(pattern)

    if not matching_files:
        logger.error(f"Could not find ttop.txt file for node {node} in {pattern}")
        metadata.analysis_state[node] = AnalysisState.SKIPPED
        return metadata.analysis_state[node]

    ttop_file = Path(matching_files[0])
    if not ttop_file.is_file():
        logger.error(f"Found path is not a file: {ttop_file}")
        metadata.analysis_state[node] = AnalysisState.SKIPPED
        return metadata.analysis_state[node]

    try:
        # Initialize new data collections
        time_data: List[datetime] = []
        load_1min: List[float] = []
        load_5min: List[float] = []
        load_15min: List[float] = []
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

        with open(ttop_file) as f:
            for line in f:
                if not _maybe_parse_time_and_load_average_line(
                    time_data, load_1min, load_5min, load_15min, line
                ):
                    parse_cpu_line(cpu_data, line)

            metadata.cpu_usage[node] = cpu_data
            metadata.top_times[node] = time_data
            metadata.load_avg_1min[node] = load_1min
            metadata.load_avg_5min[node] = load_5min
            metadata.load_avg_15min[node] = load_15min
            metadata.analysis_state[node] = AnalysisState.COMPLETED
    except Exception as e:
        logger.error(f"Error reading ttop file {ttop_file}: {e}")
        metadata.analysis_state[node] = AnalysisState.FAILED

    return metadata.analysis_state[node]
