import logging
from glob import glob
from pathlib import Path
from typing import Optional

from ddcheck.storage import DdcheckMetadata

logger = logging.getLogger(__name__)


def analyse_top_output(metadata: DdcheckMetadata, node: str) -> Optional[int]:
    """
    Analyze top output for a specific node.

    :param metadata: Metadata about the uploaded tarball
    :param node: Name of the node to analyze
    :return: Number of CPU measurements found, or None if an error occurred
    """
    # Verify node exists in metadata
    if node not in metadata.nodes:
        logger.error(f"Node {node} not found in metadata nodes: {metadata.nodes}")
        return None

    # Find ttop directory for node
    extract_path = Path(metadata.extract_path)
    pattern = str(extract_path / "*" / "ttop" / node / "ttop.txt")
    matching_files = glob(pattern)

    if not matching_files:
        logger.error(f"Could not find ttop.txt file for node {node} in {pattern}")
        return None

    ttop_file = Path(matching_files[0])
    if not ttop_file.is_file():
        logger.error(f"Found path is not a file: {ttop_file}")
        return None

    # Initialize CPU data collections
    cpu_data: dict[str, list[float]] = {
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
                if line.startswith("%Cpu(s):"):
                    # Remove "%Cpu(s):" prefix and split by comma
                    cpu_parts = line.replace("%Cpu(s):", "").strip().split(",")

                    # Process each CPU measurement
                    for part in cpu_parts:
                        value_str, key = part.strip().split()
                        cpu_data[key].append(float(value_str))

            # Only store data if we found any measurements
            if any(cpu_data.values()):
                if metadata.node_cpu_data is None:
                    metadata.node_cpu_data = {}
                metadata.node_cpu_data[node] = cpu_data
                return len(cpu_data["us"])  # Return number of measurements
            return 0

    except Exception as e:
        logger.error(f"Error reading ttop file {ttop_file}: {e}")
        return None
