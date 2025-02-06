from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class DdcheckMetadata:
    original_filename: str
    ddcheck_id: str
    upload_time: datetime
    extract_path: str
    nodes: list[str]
    # CPU usage per node.
    # Each node is associated to a dict containing a list of values for keys us, sy, ni, id, wa, hi, si, st
    cpu_usage: dict[str, dict[str, list[float]]]
    # Tracks state per node: "not_started", "in_progress", "completed", "failed"
    analysis_state: dict[str, str]

    @classmethod
    def from_dict(cls, data: dict) -> "DdcheckMetadata":
        data["upload_time"] = datetime.fromisoformat(data["upload_time"])
        data["nodes"] = data["nodes"]
        data["cpu_usage"] = data.get("cpu_usage", {})
        data["analysis_state"] = data.get("analysis_state", {})
        return cls(**data)

    def to_dict(self) -> dict:
        return {
            "original_filename": self.original_filename,
            "ddcheck_id": self.ddcheck_id,
            "upload_time": self.upload_time.isoformat(),
            "extract_path": self.extract_path,
            "nodes": self.nodes,
            "cpu_usage": self.cpu_usage or {},
            "analysis_state": self.analysis_state or {},
        }


EXTRACT_DIRECTORY = Path("/tmp/extracts")

# Create extracts directory if it does not exist
EXTRACT_DIRECTORY.mkdir(parents=True, exist_ok=True)
