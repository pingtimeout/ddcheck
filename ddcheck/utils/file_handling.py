import json
import tarfile
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class DdcheckMetadata:
    original_filename: str
    ddcheck_id: str
    upload_time: datetime
    extract_path: str

    @classmethod
    def from_dict(cls, data: dict) -> "DdcheckMetadata":
        data["upload_time"] = datetime.fromisoformat(data["upload_time"])
        return cls(**data)

    def to_dict(self) -> dict:
        return {
            "original_filename": self.original_filename,
            "ddcheck_id": self.ddcheck_id,
            "upload_time": self.upload_time.isoformat(),
            "extract_path": self.extract_path,
        }


# Create uploads and extracts directories if they don't exist
UPLOAD_DIRECTORY = Path("/tmp/uploads")
EXTRACT_DIRECTORY = Path("/tmp/extracts")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
EXTRACT_DIRECTORY.mkdir(parents=True, exist_ok=True)


def save_uploaded_file(uploaded_file):
    """
    Extract the uploaded tarball and save metadata.

    :param uploaded_file: Uploaded file object
    :return: Path to the extracted directory
    """
    # Create a unique directory for this upload
    extract_id = str(uuid.uuid4())
    extract_path = EXTRACT_DIRECTORY / extract_id
    extract_path.mkdir()

    # Save tarball temporarily to extract it
    temp_tarball = UPLOAD_DIRECTORY / f"{extract_id}.tar.gz"
    with open(temp_tarball, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Extract the tarball
    with tarfile.open(temp_tarball) as tar:
        tar.extractall(path=extract_path)

    # Create metadata
    metadata = DdcheckMetadata(
        original_filename=uploaded_file.name,
        ddcheck_id=extract_id,
        upload_time=datetime.utcnow(),
        extract_path=str(extract_path),
    )

    metadata_file = extract_path / "ddcheck-metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata.to_dict(), f, indent=2)

    # Clean up temporary tarball
    temp_tarball.unlink()

    return extract_path


def get_all_metadata() -> list[DdcheckMetadata]:
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
