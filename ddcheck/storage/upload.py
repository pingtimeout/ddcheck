import json
import logging
import shutil
import tarfile
import uuid
from datetime import datetime
from typing import Optional

from streamlit.runtime.uploaded_file_manager import UploadedFile

from ddcheck.storage import EXTRACT_DIRECTORY, DdcheckMetadata

# Configure logging
logger = logging.getLogger(__name__)


def save_uploaded_tarball(uploaded_file: UploadedFile) -> Optional[DdcheckMetadata]:
    """
    Extract the uploaded tarball and save metadata.

    :param uploaded_file: Uploaded file object
    :return: Path to the extracted directory
    """
    filename = uploaded_file.name
    logger.debug(f"Starting to process {filename}")

    # Check if the file is a tarball (.tar.gz or .tgz), if not, return None
    if not filename.endswith(".tar.gz") and not filename.endswith(".tgz"):
        logger.error(f"Invalid file type: {filename} (must end with .tar.gz)")
        return None

    # Create a unique directory for this upload
    extract_id = str(uuid.uuid4())
    extract_path = EXTRACT_DIRECTORY / extract_id
    extract_path.mkdir()
    logger.debug(f"Created extraction directory at {extract_path}")

    # Extract the tarball and delete it
    valid = True
    try:
        logger.debug("Extracting tarball contents")
        with tarfile.open(fileobj=uploaded_file) as tar:
            tar.extractall(path=extract_path)
    except tarfile.ReadError:
        # The tarball could not be read, mark it as invalid
        logger.error("Failed to read tarball - file might be corrupted")
        valid = False

    # A valid tarball should have a summary.json file
    summary_file = extract_path / "summary.json"
    valid = valid and summary_file.exists()
    if not summary_file.exists():
        logger.error("Missing summary.json file in uploaded tarball")

    # If the tarball is invalid, delete the extract directory and return None
    if not valid:
        logger.error("Invalid tarball structure - cleaning up extraction directory")
        shutil.rmtree(extract_path)
        return None

    # Read the summary.json file and collect node names
    logger.debug("Reading summary.json and collecting node information")
    with open(summary_file) as f:
        summary_data = json.load(f)
        executors = summary_data.get("executors", [])
        coordinators = summary_data.get("coordinators", [])
        nodes = executors + coordinators
    logger.debug(f"Found {len(nodes)} nodes in the cluster data")

    # Create metadata
    metadata = DdcheckMetadata(
        original_filename=filename,
        ddcheck_id=extract_id,
        upload_time=datetime.utcnow(),
        extract_path=str(extract_path),
        nodes=nodes,
        cpu_usage={},
        analysis_state={node: "not_started" for node in nodes},
    )

    metadata_file = extract_path / "ddcheck-metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata.to_dict(), f, indent=2)
    logger.debug(f"Successfully processed {filename}")

    return metadata
