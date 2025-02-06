import json
import tarfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from ddcheck.utils import DdcheckMetadata

# Create uploads and extracts directories if they don't exist
UPLOAD_DIRECTORY = Path("/tmp/uploads")
EXTRACT_DIRECTORY = Path("/tmp/extracts")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
EXTRACT_DIRECTORY.mkdir(parents=True, exist_ok=True)


def save_uploaded_tarball(uploaded_file) -> Optional[DdcheckMetadata]:
    """
    Extract the uploaded tarball and save metadata.

    :param uploaded_file: Uploaded file object
    :return: Path to the extracted directory
    """
    # Check if the file is a tarball, if not, return None
    if not uploaded_file.name.endswith(".tar.gz"):
        return None

    # Create a unique directory for this upload
    extract_id = str(uuid.uuid4())
    extract_path = EXTRACT_DIRECTORY / extract_id
    extract_path.mkdir()

    # Save tarball temporarily to extract it
    temp_tarball = UPLOAD_DIRECTORY / f"{extract_id}.tar.gz"
    with open(temp_tarball, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Extract the tarball and delete it
    valid = True
    try:
        with tarfile.open(temp_tarball) as tar:
            tar.extractall(path=extract_path)
    except tarfile.ReadError:
        # The tarball could not be read, mark it as invalid
        valid = False
    temp_tarball.unlink()

    # A valid tarball should have a `ttop` directory
    valid = valid and (extract_path / "ttop").exists()

    # If the tarball is invalid, delete the extract directory and return None
    if not valid:
        extract_path.rmdir()
        return None

    # Collect all subdirectory names in the ttop directory
    ttop_path = extract_path / "ttop"
    nodes = [d.name for d in ttop_path.iterdir() if d.is_dir()]

    # Create metadata
    metadata = DdcheckMetadata(
        original_filename=uploaded_file.name,
        ddcheck_id=extract_id,
        upload_time=datetime.utcnow(),
        extract_path=str(extract_path),
        nodes=nodes,
    )

    metadata_file = extract_path / "ddcheck-metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata.to_dict(), f, indent=2)

    return metadata


def list_all_uploaded_tarballs() -> list[DdcheckMetadata]:
    """
    Find all extracted tarballs and return their metadata.

    :return: List of DdcheckMetadata objects
    """
    results = []
    for extract_dir in EXTRACT_DIRECTORY.iterdir():
        metadata_file = extract_dir / "ddcheck-metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata_dict = json.load(f)
                results.append(DdcheckMetadata.from_dict(metadata_dict))
    return results
