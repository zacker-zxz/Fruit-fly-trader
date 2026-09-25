"""Connectome processor: raw edge list -> computational subgraph.

Preserves topology of the sampled subset. Sampling keeps high-weight hubs plus
a uniform random complement so the degree distribution is not artificially
destroyed.
"""

import csv
import random
from dataclasses import dataclass, field


@dataclass
class Edge:
    src: int
    tgt: int
    weight: float


@dataclass
class Connectome:
    """Sparse adjacency structure with index mapping."""

    ids: list[int]
    index: dict[int, int]
    edges: list[Edge]
    out_edges: dict[int, list[int]] = field(default_factory=dict)
    in_edges: dict[int, list[int]] = field(default_factory=dict)

    @property
    def n_neurons(self) -> int:
        return len(self.ids)

    @property
    def n_synapses(self) -> int:
        return len(self.edges)


def load_edge_list(path: str) -> list[Edge]:
    edges = []
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        # tolerate both raw flyconnectome columns and simplified src,tgt,weight
        try:
            si = next(i for i, h in enumerate(header) if h.lower() in ("src", "src_id", "pre_root_id", "pre"))
            ti = next(i for i, h in enumerate(header) if h.lower() in ("tgt", "tgt_id", "post_root_id", "post"))
            wi = next((i for i, h in enumerate(header) if h.lower() in ("weight", "syn_count", "n")), None)
        except StopIteration:
            raise ValueError(f"unrecognized connectome schema: {header}")
        for row in reader:
            src = int(row[si])
            tgt = int(row[ti])
            if src == tgt:
                continue
            w = float(row[wi]) if wi is not None else 1.0
            if w > 0:
                edges.append(Edge(src, tgt, w))
    return edges


def sample(edges: list[Edge], max_neurons: int, seed: int = 0) -> Connectome:
    """Sample a connected-ish subgraph within budget, preserving hub topology."""
    rng = random.Random(seed)
    degree: dict[int, int] = {}
    for e in edges:
        degree[e.src] = degree.get(e.src, 0) + 1
        degree[e.tgt] = degree.get(e.tgt, 0) + 1
    if len(degree) <= max_neurons:
        keep = set(degree)
    else:
        ranked = sorted(degree, key=lambda n: degree[n], reverse=True)
        n_hubs = max_neurons // 4
        hubs = set(ranked[:n_hubs])
        rest = rng.sample(ranked[n_hubs:], max_neurons - n_hubs)
        keep = hubs | set(rest)
    ids = sorted(keep)
    index = {n: i for i, n in enumerate(ids)}
    sub = [e for e in edges if e.src in keep and e.tgt in keep]
    out_edges: dict[int, list[int]] = {}
    in_edges: dict[int, list[int]] = {}
    for j, e in enumerate(sub):
        out_edges.setdefault(index[e.src], []).append(j)
        in_edges.setdefault(index[e.tgt], []).append(j)
    return Connectome(ids=ids, index=index, edges=sub, out_edges=out_edges, in_edges=in_edges)


def from_file(path: str, max_neurons: int, seed: int = 0) -> Connectome:
    return sample(load_edge_list(path), max_neurons, seed)
