from dataclasses import dataclass
from datetime import datetime


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
