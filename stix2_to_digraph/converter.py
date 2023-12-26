import json
from typing import Iterable, Optional, Union
import networkx as nx
from stix2.datastore import DataSource
from dataclasses import dataclass
import re
from typing import Iterable, List
import os
import requests
from stix2 import (
    FileSystemSource,
    MemoryStore,
    CompositeDataSource,
)
from stix2.datastore import DataSource
from stix2 import Filter
from typing import Iterable, Union

CREATED = "created"
MODIFIED = "modified"
RELATED_TO = "related-to"


@dataclass()
class Converter:
    data_source: Union[str, MemoryStore, DataSource]
    add_created_by_ref: bool = False
    add_modified_by_ref: bool = False

    def __post_init__(self):
        self.data_source = get_data_source(self.data_source)

    def stix2_to_networkx(
        self, query: Optional[str] = None, compact: bool = True
    ) -> nx.DiGraph:
        """
        Creates a nx.DiGraph from a list of STIX 2 objects.

        - Nodes only contain IDs or URLs
        - Edges only contain labels
        """
        g = nx.DiGraph()
        objects = self.data_source.query(query)
        for o in objects:
            stix2_id = o["id"]
            if compact:
                g.add_node(stix2_id)
            else:
                g.add_node(stix2_id, **o)

            if o["type"] == "relationship":
                g.add_edge(
                    o["source_ref"],
                    o["target_ref"],
                    relationship_type=o["relationship_type"],
                )
            else:
                g.add_node(stix2_id)

            if self.add_created_by_ref:
                created_by = o.get("created_by_ref")
                if created_by:
                    g.add_edge(created_by, stix2_id, relationship_type=CREATED)

            if self.add_modified_by_ref:
                modified_by = o.get("x_mitre_modified_by_ref")
                if modified_by:
                    g.add_edge(modified_by, stix2_id, relationship_type=MODIFIED)
        return g


def networkx_to_dot(g: nx.DiGraph) -> str:
    lines = []
    lines.append("digraph {")

    # Nodes
    for _, o in g.nodes(data=True):
        if o["type"] == "marking-definition":
            continue

        object_id = o["id"].replace("-", "_")
        label = o["name"]
        lines.append(f'  {object_id} [label="{label}"]')

    lines.append("")

    # Edges
    for a, b in g.edges:
        a = a.replace("-", "_")
        b = b.replace("-", "_")
        lines.append(f"  {a} -> {b}")
    lines.append("}")

    return "\n".join(lines)


def get_data_sources(
    data_sources: Iterable[Union[str, DataSource]]
) -> Iterable[DataSource]:
    return [get_data_source(src) for src in data_sources]


def get_composite_data_source(data_sources: Iterable[Union[str, DataSource]]):
    composite = CompositeDataSource()
    for data_source in data_sources:
        composite.add_data_source(get_data_source(data_source))
    return composite


def get_data_source(data_source: Union[str, DataSource]) -> DataSource:
    if isinstance(data_source, (DataSource, MemoryStore)):
        return data_source
    elif isinstance(data_source, str):
        return _get_data_source(data_source)
    else:
        raise ValueError(f"Invalid data source: {data_source}")


def _get_data_source(path: str) -> DataSource:
    if os.path.exists(path):
        if os.path.isdir(path):
            return FileSystemSource(path)
        else:
            return _get_memory_store_from_file(path)
    elif path.startswith(("http://", "https://")):
        return _get_memory_store_from_web(path)
    else:
        raise ValueError(f"Invalid path: {path}")


def _get_memory_store_from_file(path: str) -> MemoryStore:
    with open(path, "r") as file:
        stix_data = json.load(file)
        return MemoryStore(stix_data=stix_data)


def _get_memory_store_from_web(url: str) -> MemoryStore:
    response = requests.get(url)
    response.raise_for_status()
    return MemoryStore(response.json()["objects"])


def parse_stix2_filters(stix2_filters: Iterable[Union[str, Filter]]) -> List[Filter]:
    return [parse_stix2_filter(f) for f in stix2_filters]


def parse_stix2_filter(stix2_filter: str) -> Filter:
    """
    The following operators are supported:

    - '='
    - '!='
    - 'in'
    - '>'
    - '<'
    - '>='
    - '<='
    - 'contains'
    """
    m = re.match(r"(.+) (.+) (.+)", stix2_filter)
    if m:
        k, o, v = m.groups()
        return Filter(k, o, v)


def realpath(path: str) -> str:
    path = os.path.expanduser(path)
    path = os.path.realpath(path)
    return path
