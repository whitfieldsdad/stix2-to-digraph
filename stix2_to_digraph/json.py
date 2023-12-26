import dataclasses
import json
from typing import Any
from stix2.serialization import STIXJSONEncoder as _JSONEncoder
from stix2.base import _STIXBase
from stix2.utils import STIXdatetime
import networkx as nx
from concurrent.futures import ThreadPoolExecutor
import networkx.readwrite.json_graph as json_graph
import concurrent.futures
import logging

logger = logging.getLogger(__name__)


class JSONEncoder(_JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, nx.DiGraph):
            return json_graph.node_link_data(o)
        elif dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        elif isinstance(o, _STIXBase):
            return dict(o)
        elif isinstance(o, STIXdatetime):
            return o.isoformat()
        elif iter(o) == o:
            return list(o)
        else:
            return super().default(o)


def dumps(o: Any, **kwargs) -> str:
    return json.dumps(o, cls=JSONEncoder)


def loads(s: str, **kwargs) -> Any:
    return json.loads(s, **kwargs)


def load(f, **kwargs) -> Any:
    return json.load(f, **kwargs)


def read_json_files(
    *paths: str,
) -> Any:
    with ThreadPoolExecutor() as executor:
        futures = []
        for path in paths:
            future = executor.submit(read_json_file, path)
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            yield future.result()


def read_json_file(path: str) -> Any:
    logger.debug(f"Reading {path}")
    with open(path, "r") as f:
        return load(f)
