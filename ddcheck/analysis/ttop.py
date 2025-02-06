import logging
from glob import glob
from pathlib import Path
from typing import Optional

from ddcheck.storage import DdcheckMetadata

logger = logging.getLogger(__name__)


def analyse_top_output(metadata: DdcheckMetadata, node: str) -> Optional[int]:
    """
    Analyze ttop output for a specific node.

    :param metadata: Metadata about the uploaded tarball
    :param node: Name of the node to analyze
    :return: Number of lines in ttop.txt file, or None if an error occurred
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

    try:
        with open(ttop_file) as f:
            return sum(1 for _ in f)
    except Exception as e:
        logger.error(f"Error reading ttop file {ttop_file}: {e}")
        return None
