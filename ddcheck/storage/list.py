import json
from typing import Optional

from ddcheck.storage import EXTRACT_DIRECTORY, DdcheckMetadata


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


def get_uploaded_metadata(ddcheck_id: str) -> Optional[DdcheckMetadata]:
    """
    Retrieve metadata for a specific upload ID.

    :param ddcheck_id: Unique ID for the upload
    :return: DdcheckMetadata object if found, otherwise None
    """
    extract_path = EXTRACT_DIRECTORY / ddcheck_id
    metadata_file = extract_path / "ddcheck-metadata.json"
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata_dict = json.load(f)
            return DdcheckMetadata.from_dict(metadata_dict)
    return None
