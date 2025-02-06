import json
import logging
import tarfile
import uuid
from datetime import datetime
from typing import Optional

from ddcheck.storage import EXTRACT_DIRECTORY, UPLOAD_DIRECTORY, DdcheckMetadata

# Configure logging
logger = logging.getLogger(__name__)


def save_uploaded_tarball(uploaded_file) -> Optional[DdcheckMetadata]:
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

    # Save tarball temporarily to extract it
    temp_tarball = UPLOAD_DIRECTORY / f"{extract_id}.tar.gz"
    with open(temp_tarball, "wb") as f:
        f.write(uploaded_file.getbuffer())
    logger.debug("Saved temporary tarball")

    # Extract the tarball and delete it
    valid = True
    try:
        logger.debug("Extracting tarball contents")
        with tarfile.open(temp_tarball) as tar:
            tar.extractall(path=extract_path)
    except tarfile.ReadError:
        # The tarball could not be read, mark it as invalid
        logger.error("Failed to read tarball - file might be corrupted")
        valid = False
    temp_tarball.unlink()
    logger.debug("Cleaned up temporary tarball")

    # A valid tarball should have a summary.json file
    summary_file = extract_path / "summary.json"
    valid = valid and summary_file.exists()
    if not summary_file.exists():
        logger.error("Missing summary.json file in uploaded tarball")

    # If the tarball is invalid, delete the extract directory and return None
    if not valid:
        logger.error("Invalid tarball structure - cleaning up extraction directory")
        extract_path.rmdir()
        return None

    # Read the summary.json file and collect node names
    logger.debug("Reading summary.json and collecting node information")
    with open(summary_file) as f:
        summary_data = json.load(f)
        nodes = list(summary_data.get("dremioVersion", {}).keys())
    logger.debug(f"Found {len(nodes)} nodes in the cluster data")

    # Create metadata
    metadata = DdcheckMetadata(
        original_filename=filename,
        ddcheck_id=extract_id,
        upload_time=datetime.utcnow(),
        extract_path=str(extract_path),
        nodes=nodes,
        cpu_usage={},
    )

    metadata_file = extract_path / "ddcheck-metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata.to_dict(), f, indent=2)
    logger.debug(f"Successfully processed {filename}")

    return metadata
