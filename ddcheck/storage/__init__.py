import functools
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any


class Source(Enum):
    TOP = auto()
    OS_INFO = auto()

    def to_str(self) -> str:
        return self.name.lower()

    @classmethod
    def from_str(cls, source: str) -> "Source":
        return Source[source.upper()]


class AnalysisState(Enum):
    NOT_STARTED = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()

    def to_str(self) -> str:
        return self.name.lower()

    @classmethod
    def from_str(cls, state: str) -> "AnalysisState":
        return AnalysisState[state.upper()]

    def max(self, other: "AnalysisState") -> "AnalysisState":
        """Returns the state with the higher priority between self and other.

        Priority order (highest to lowest):
        1. FAILED
        2. IN_PROGRESS
        3. COMPLETED
        4. SKIPPED
        5. NOT_STARTED

        Args:
            other: Another analysis state to compare against

        Returns:
            AnalysisState representing the most important state
        """
        if AnalysisState.FAILED in (self, other):
            return AnalysisState.FAILED

        if AnalysisState.IN_PROGRESS in (self, other):
            return AnalysisState.IN_PROGRESS

        if AnalysisState.COMPLETED in (self, other):
            return AnalysisState.COMPLETED

        if AnalysisState.SKIPPED in (self, other):
            return AnalysisState.SKIPPED

        return AnalysisState.NOT_STARTED


class InsightQualifier(Enum):
    OK = auto()
    INTERESTING = auto()
    BAD = auto()
    CHECK = auto()

    def to_str(self) -> str:
        return self.name.lower()

    @classmethod
    def from_str(cls, qualifier: str) -> "InsightQualifier":
        return InsightQualifier[qualifier.upper()]


class Insight:
    node: str
    source: Source
    qualifier: InsightQualifier
    message: str

    def __init__(
        self, node: str, source: Source, qualifier: InsightQualifier, message: str
    ):
        self.node = node
        self.source = source
        self.qualifier = qualifier
        self.message = message

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Insight):
            return False
        return (
            self.node == other.node
            and self.source == other.source
            and self.qualifier == other.qualifier
            and self.message == other.message
        )

    def __hash__(self) -> int:
        return hash((self.node, self.source, self.qualifier, self.message))

    def to_dict(self) -> dict:
        return {
            "node": self.node,
            "source": self.source.to_str(),
            "qualifier": self.qualifier.to_str(),
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Insight":
        return Insight(
            node=data["node"],
            source=Source.from_str(data["source"]),
            qualifier=InsightQualifier.from_str(data["qualifier"]),
            message=data["message"],
        )


class DdcheckMetadata:
    original_filename: str
    ddcheck_id: str
    upload_time: datetime
    extract_path: str
    nodes: list[str]
    analysis_state: dict[str, dict[Source, AnalysisState]]
    insights: set[Insight]
    # CPU usage per node.
    # Each node is associated to a dict containing a list of values for keys us, sy, ni, id, wa, hi, si, st
    cpu_usage: dict[str, dict[str, list[float]]]
    # Times when top was executed per node (stored as datetime objects)
    top_times: dict[str, list[datetime]]
    # Load averages per node. Each node has three lists for 1min, 5min, and 15min averages
    load_avg_1min: dict[str, list[float]]
    load_avg_5min: dict[str, list[float]]
    load_avg_15min: dict[str, list[float]]
    # Tracks State per node and source
    total_memory_kb: dict[str, int]

    def __init__(
        self,
        original_filename: str,
        ddcheck_id: str,
        upload_time: datetime,
        extract_path: str,
        nodes: list[str],
    ):
        self.original_filename = original_filename
        self.ddcheck_id = ddcheck_id
        self.upload_time = upload_time
        self.extract_path = extract_path
        self.nodes = nodes
        self.reset()

    def reset(self) -> None:
        """Resets the analysis state and insights."""
        self.analysis_state = {
            node: {source: AnalysisState.NOT_STARTED for source in Source}
            for node in self.nodes
        }
        self.insights = set()
        self.cpu_usage = {}
        self.top_times = {node: [] for node in self.nodes}
        self.load_avg_1min = {node: [] for node in self.nodes}
        self.load_avg_5min = {node: [] for node in self.nodes}
        self.load_avg_15min = {node: [] for node in self.nodes}
        self.total_memory_kb = {}

    @classmethod
    def from_dict(cls, data: dict) -> "DdcheckMetadata":
        metadata = DdcheckMetadata(
            original_filename=data["original_filename"],
            ddcheck_id=data["ddcheck_id"],
            upload_time=datetime.fromisoformat(data["upload_time"]),
            extract_path=data["extract_path"],
            nodes=data["nodes"],
        )
        metadata.analysis_state = {
            node: {
                Source.from_str(source): AnalysisState.from_str(state)
                for source, state in states.items()
            }
            for node, states in data.get("analysis_state", {}).items()
        }
        metadata.insights = {
            Insight.from_dict(insight) for insight in data.get("insights", [])
        }
        metadata.cpu_usage = data.get("cpu_usage", {})
        metadata.top_times = {
            node: [datetime.strptime(t, "%H:%M:%S") for t in times]
            for node, times in data.get("top_times", {}).items()
        }
        metadata.load_avg_1min = data.get("load_avg_1min", {})
        metadata.load_avg_5min = data.get("load_avg_5min", {})
        metadata.load_avg_15min = data.get("load_avg_15min", {})
        metadata.total_memory_kb = data.get("total_memory_kb", {})
        return metadata

    def to_dict(self) -> dict:
        return {
            "original_filename": self.original_filename,
            "ddcheck_id": self.ddcheck_id,
            "upload_time": self.upload_time.isoformat(),
            "extract_path": self.extract_path,
            "nodes": self.nodes,
            "insights": [insight.to_dict() for insight in self.insights],
            "cpu_usage": self.cpu_usage or {},
            "top_times": {
                node: [t.strftime("%H:%M:%S") for t in times]
                for node, times in self.top_times.items()
            },
            "load_avg_1min": self.load_avg_1min or {},
            "load_avg_5min": self.load_avg_5min or {},
            "load_avg_15min": self.load_avg_15min or {},
            "analysis_state": {
                node: {
                    source.to_str(): state.to_str() for source, state in states.items()
                }
                for node, states in self.analysis_state.items()
            },
            "total_memory_kb": self.total_memory_kb or {},
        }

    def get_overall_analysis_state(self) -> AnalysisState:
        """Returns the overall analysis state by reducing all node and source states.

        If there are no nodes, returns NOT_STARTED.
        Otherwise reduces all states using priority rules.

        Returns:
            AnalysisState representing the overall state of all nodes and sources
        """
        if not self.nodes:
            return AnalysisState.NOT_STARTED

        # Get all states from all nodes and sources
        all_states = (
            state
            for node in self.nodes
            for state in self.analysis_state.get(node, {}).values()
        )

        # Start with lowest priority and reduce all states
        return functools.reduce(
            lambda state1, state2: state1.max(state2),
            all_states,
            AnalysisState.NOT_STARTED,
        )

    def insights_per_node_and_qualifier(
        self,
    ) -> dict[str, dict[InsightQualifier, list[Insight]]]:
        # Initialize a dictionary with all nodes and qualifiers
        result: dict[str, dict[InsightQualifier, list[Insight]]] = {
            node: {qualifier: [] for qualifier in InsightQualifier}
            for node in self.nodes
        }
        # Group insights by node and qualifier
        for insight in self.insights:
            result[insight.node][insight.qualifier].append(insight)
        # Sorting each group by source and then message
        for node in result:
            for qualifier in result[node]:
                result[node][qualifier] = sorted(
                    result[node][qualifier], key=lambda i: (i.source, i.message)
                )
        return result

    def insights_per_qualifier_and_node(
        self,
    ) -> dict[InsightQualifier, dict[str, list[Insight]]]:
        # Initialize a dictionary with all qualifiers and nodes
        result: dict[InsightQualifier, dict[str, list[Insight]]] = {
            qualifier: {node: [] for node in self.nodes}
            for qualifier in InsightQualifier
        }
        # Group insights by qualifier and node
        for insight in self.insights:
            result[insight.qualifier][insight.node].append(insight)
        # Sorting each group by source and then message
        for qualifier in result:
            for node in result[qualifier]:
                result[qualifier][node] = sorted(
                    result[qualifier][node], key=lambda i: (i.source, i.message)
                )
        return result


EXTRACT_DIRECTORY = Path("/tmp/extracts")

# Create extracts directory if it does not exist
EXTRACT_DIRECTORY.mkdir(parents=True, exist_ok=True)
