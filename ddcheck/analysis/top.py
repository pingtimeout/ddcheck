import logging
from datetime import datetime
from glob import glob
from pathlib import Path
from typing import Dict, List

from ddcheck.storage import (
    AnalysisState,
    DdcheckMetadata,
    Insight,
    InsightQualifier,
    Source,
)

logger = logging.getLogger(__name__)


def analyse_top_output(metadata: DdcheckMetadata, node: str) -> AnalysisState:
    # If node does not exist in metadata, log an error and mark it as skipped
    if node not in metadata.nodes:
        logger.error(f"Node {node} not found in metadata nodes: {metadata.nodes}")
        metadata.analysis_state[node][Source.TOP] = AnalysisState.SKIPPED

    # Skip the analysis if it has already been attempted
    current_state = metadata.analysis_state.get(node, {}).get(
        Source.TOP, AnalysisState.NOT_STARTED
    )
    if current_state != AnalysisState.NOT_STARTED:
        logger.debug(f"Skipping analysis for node {node} - state is {current_state}")
        return current_state

    # Mark analysis as in progress
    metadata.analysis_state[node][Source.TOP] = AnalysisState.IN_PROGRESS

    # Find ttop directory for node
    extract_path = Path(metadata.extract_path)
    pattern = str(extract_path / "*" / "ttop" / node / "ttop.txt")
    matching_files = glob(pattern)

    if not matching_files:
        logger.error(f"Could not find ttop.txt file for node {node} in {pattern}")
        metadata.analysis_state[node][Source.TOP] = AnalysisState.SKIPPED
        return metadata.analysis_state[node][Source.TOP]

    ttop_file = Path(matching_files[0])
    if not ttop_file.is_file():
        logger.error(f"Found path is not a file: {ttop_file}")
        metadata.analysis_state[node][Source.TOP] = AnalysisState.SKIPPED
        return metadata.analysis_state[node][Source.TOP]

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
            "total": [],
            "jpdm": [],
        }

        with open(ttop_file) as f:
            for line in f:
                if not _maybe_parse_time_and_load_average_line(
                    time_data, load_1min, load_5min, load_15min, line
                ):
                    _maybe_parse_cpu_line(cpu_data, line)

            metadata.cpu_usage[node] = cpu_data
            metadata.top_times[node] = time_data
            metadata.load_avg_1min[node] = load_1min
            metadata.load_avg_5min[node] = load_5min
            metadata.load_avg_15min[node] = load_15min
            metadata.analysis_state[node][Source.TOP] = AnalysisState.COMPLETED
    except Exception as e:
        logger.exception(e)
        logger.error(f"Error reading ttop file {ttop_file}: {e}")
        metadata.analysis_state[node][Source.TOP] = AnalysisState.FAILED

    _check_cpu_wa(metadata, node)
    _check_cpu_st(metadata, node)
    _check_cpu_usage(metadata, node)
    _check_jpdm(metadata, node)
    _check_load_average(metadata, node)

    return metadata.analysis_state[node][Source.TOP]


def _maybe_parse_cpu_line(cpu_data: Dict[str, List[float]], line: str) -> bool:
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

    # Compute total CPU usage
    total = 100 - cpu_data["id"][-1]
    cpu_data["total"].append(total)

    # Compute ratio between CPU sy and CPU us
    cpu_sy = cpu_data["sy"][-1]
    cpu_us = cpu_data["us"][-1]
    if cpu_us == 0 and cpu_sy == 0:
        jpdm = 0.0
    else:
        if cpu_us == 0:
            cpu_us = cpu_sy * 10
        jpdm = cpu_sy / cpu_us * 100
    cpu_data["jpdm"].append(jpdm)

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


def _check_cpu_wa(metadata: DdcheckMetadata, node: str) -> None:
    # Record a CHECK insight for checking the average CPU time spent waiting for I/O.
    metadata.insights.add(
        Insight(
            node=node,
            source=Source.TOP,
            qualifier=InsightQualifier.CHECK,
            message="Checking the average CPU time spent waiting for I/O",
        )
    )

    avg_cpu_wa = sum(metadata.cpu_usage[node]["wa"]) / len(
        metadata.cpu_usage[node]["wa"]
    )
    if avg_cpu_wa >= 6:
        metadata.insights.add(
            Insight(
                node=node,
                source=Source.TOP,
                qualifier=InsightQualifier.BAD,
                message=f"High average CPU time spent waiting for disk I/O: {avg_cpu_wa:.1f}%",
            )
        )
    elif avg_cpu_wa >= 1:
        metadata.insights.add(
            Insight(
                node=node,
                source=Source.TOP,
                qualifier=InsightQualifier.INTERESTING,
                message=f"Non-zero average CPU time spent waiting for disk I/O: {avg_cpu_wa:.1f}%",
            )
        )
    else:
        metadata.insights.add(
            Insight(
                node=node,
                source=Source.TOP,
                qualifier=InsightQualifier.OK,
                message="No time spent waiting for disk I/O, suggesting no disk saturation",
            )
        )


def _check_cpu_usage(metadata: DdcheckMetadata, node: str) -> None:
    # Record a CHECK insight for checking the average CPU time spent waiting for I/O.
    metadata.insights.add(
        Insight(
            node=node,
            source=Source.TOP,
            qualifier=InsightQualifier.CHECK,
            message="Checking the average CPU usage",
        )
    )

    avg_cpu_usage = sum(metadata.cpu_usage[node]["total"]) / len(
        metadata.cpu_usage[node]["total"]
    )
    if avg_cpu_usage > 60:
        metadata.insights.add(
            Insight(
                node=node,
                source=Source.TOP,
                qualifier=InsightQualifier.BAD,
                message=f"High average CPU usage: {avg_cpu_usage:.0f}%",
            )
        )


def _check_cpu_st(metadata: DdcheckMetadata, node: str) -> None:
    # Record a CHECK insight for checking the average CPU time spent waiting for I/O.
    metadata.insights.add(
        Insight(
            node=node,
            source=Source.TOP,
            qualifier=InsightQualifier.CHECK,
            message="Checking the average stolen CPU time",
        )
    )

    avg_cpu_usage = sum(metadata.cpu_usage[node]["st"]) / len(
        metadata.cpu_usage[node]["st"]
    )
    if avg_cpu_usage >= 1:
        metadata.insights.add(
            Insight(
                node=node,
                source=Source.TOP,
                qualifier=InsightQualifier.BAD,
                message=f"Non-zero stolen CPU time: {avg_cpu_usage:.1f}%",
            )
        )


def _check_jpdm(metadata: DdcheckMetadata, node: str) -> None:
    metadata.insights.add(
        Insight(
            node=node,
            source=Source.TOP,
            qualifier=InsightQualifier.CHECK,
            message="Checking the JPDM ratio",
        )
    )

    avg_jpdm = sum(metadata.cpu_usage[node]["jpdm"]) / len(
        metadata.cpu_usage[node]["jpdm"]
    )
    avg_cpu_usage = sum(metadata.cpu_usage[node]["total"]) / len(
        metadata.cpu_usage[node]["total"]
    )

    if avg_jpdm >= 10:
        metadata.insights.add(
            Insight(
                node=node,
                source=Source.TOP,
                qualifier=InsightQualifier.INTERESTING,
                message=f"Dominating consumer of the CPU: System. JPDM ratio={avg_jpdm:.1f}%",
            )
        )
    elif avg_cpu_usage >= 90:
        metadata.insights.add(
            Insight(
                node=node,
                source=Source.TOP,
                qualifier=InsightQualifier.INTERESTING,
                message=f"Dominating consumer of the CPU: User. JPDM ratio={avg_jpdm:.1f}% and average CPU usage={avg_cpu_usage:.0f}%",
            )
        )
    else:
        metadata.insights.add(
            Insight(
                node=node,
                source=Source.TOP,
                qualifier=InsightQualifier.INTERESTING,
                message=f"Dominating consumer of the CPU: None. JPDM ratio={avg_jpdm:.1f}% and average CPU usage={avg_cpu_usage:.0f}%",
            )
        )


def _check_load_average(metadata: DdcheckMetadata, node: str) -> None:
    metadata.insights.add(
        Insight(
            node=node,
            source=Source.TOP,
            qualifier=InsightQualifier.CHECK,
            message="Checking the load averages",
        )
    )

    avg_1m_load_average = sum(metadata.load_avg_1min[node]) / len(
        metadata.load_avg_1min[node]
    )
    avg_15m_load_average = sum(metadata.load_avg_15min[node]) / len(
        metadata.load_avg_15min[node]
    )
    total_cpu_count = metadata.total_cpu_count[node]

    if avg_1m_load_average > total_cpu_count and avg_15m_load_average > total_cpu_count:
        metadata.insights.add(
            Insight(
                node=node,
                source=Source.TOP,
                qualifier=InsightQualifier.INTERESTING,
                message=f"Both 1-min load average ({avg_1m_load_average:.1f}) and 15-min load average ({avg_15m_load_average:.1f}) are higher than total CPU count ({total_cpu_count})",
            )
        )
