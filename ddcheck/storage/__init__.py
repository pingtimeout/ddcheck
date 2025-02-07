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
    # Times when top was executed per node (stored as datetime objects)
    top_times: dict[str, list[datetime]]
    # Load averages per node. Each node has three lists for 1min, 5min, and 15min averages
    load_avg_1min: dict[str, list[float]]
    load_avg_5min: dict[str, list[float]]
    load_avg_15min: dict[str, list[float]]
    # Tracks state per node: "not_started", "in_progress", "completed", "failed"
    analysis_state: dict[str, str]

    @classmethod
    def from_dict(cls, data: dict) -> "DdcheckMetadata":
        data["upload_time"] = datetime.fromisoformat(data["upload_time"])
        data["nodes"] = data["nodes"]
        data["cpu_usage"] = data.get("cpu_usage", {})
        # Convert time strings to datetime objects
        top_times_dict = data.get("top_times", {})
        data["top_times"] = {
            node: [datetime.strptime(t, "%H:%M:%S") for t in times]
            for node, times in top_times_dict.items()
        }
        data["load_avg_1min"] = data.get("load_avg_1min", {})
        data["load_avg_5min"] = data.get("load_avg_5min", {})
        data["load_avg_15min"] = data.get("load_avg_15min", {})
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
            "top_times": {
                node: [t.strftime("%H:%M:%S") for t in times]
                for node, times in self.top_times.items()
            },
            "load_avg_1min": self.load_avg_1min or {},
            "load_avg_5min": self.load_avg_5min or {},
            "load_avg_15min": self.load_avg_15min or {},
            "analysis_state": self.analysis_state or {},
        }


EXTRACT_DIRECTORY = Path("/tmp/extracts")

# Create extracts directory if it does not exist
EXTRACT_DIRECTORY.mkdir(parents=True, exist_ok=True)
