"""
bus_network.py - 33-Bus Radial Distribution Network Topology & Cable Loss Factors

Role: Models a 33-bus IEEE radial distribution network topology, mapping generation sources
(PV at Bus 13 & 30, Wind at Bus 6) and calculating cable distance loss factors.

Loss Factor Formula:
  distance = shortest_path_hops(Bus 1, Target Bus)
  loss_factor = min(1.15, 1.00 + 0.01 * distance)
"""

from collections import deque
from typing import Any, Dict, List, Tuple

CONFIG: Dict[str, Any] = {
    "root_bus": 1,
    "max_loss_factor": 1.15,
    "base_loss_factor": 1.00,
    "loss_per_hop": 0.01,
    "pv_buses": [13, 30],
    "wind_buses": [6],
}

# Standard IEEE 33-Bus Radial Topology Adjacency List (1-indexed buses)
IEEE_33_BUS_EDGES: List[Tuple[int, int]] = [
    (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11), (11, 12), (12, 13), (13, 14), (14, 15), (15, 16), (16, 17), (17, 18),
    (2, 19), (19, 20), (20, 21), (21, 22),
    (5, 23), (23, 24), (24, 25),
    (6, 26), (26, 27), (27, 28), (28, 29), (29, 30), (30, 31), (31, 32), (32, 33)
]


def build_adjacency_list() -> Dict[int, List[int]]:
    """Constructs 33-bus graph adjacency list."""
    adj: Dict[int, List[int]] = {i: [] for i in range(1, 34)}
    for u, v in IEEE_33_BUS_EDGES:
        adj[u].append(v)
        adj[v].append(u)
    return adj


_ADJACENCY = build_adjacency_list()


def compute_bus_distances(root_bus: int = 1) -> Dict[int, int]:
    """Computes shortest hop distance from root_bus (Bus 1) to all buses using BFS."""
    distances: Dict[int, int] = {i: -1 for i in range(1, 34)}
    queue = deque([root_bus])
    distances[root_bus] = 0

    while queue:
        curr = queue.popleft()
        for nbr in _ADJACENCY[curr]:
            if distances[nbr] == -1:
                distances[nbr] = distances[curr] + 1
                queue.append(nbr)

    return distances


_BUS_DISTANCES = compute_bus_distances(CONFIG["root_bus"])


def get_loss_factor(bus_id: int) -> float:
    """
    Computes estimated cable transmission loss factor for a given bus.

    Args:
        bus_id: Bus identifier (1 to 33)

    Returns:
        Loss multiplier between 1.00 (Bus 1) and 1.15 (Far end buses)
    """
    dist = _BUS_DISTANCES.get(bus_id, 0)
    loss = CONFIG["base_loss_factor"] + CONFIG["loss_per_hop"] * dist
    return float(min(CONFIG["max_loss_factor"], loss))


def get_bus_generator_mapping() -> Dict[str, List[int]]:
    """Returns mapping of generator types to bus locations."""
    return {
        "PV": CONFIG["pv_buses"].copy(),
        "Wind": CONFIG["wind_buses"].copy(),
    }


if __name__ == "__main__":
    print("--- 33-BUS NETWORK TOPOLOGY VERIFICATION ---")
    print(f"Root Bus: Bus {CONFIG['root_bus']}")
    for bus_id in [1, 6, 13, 18, 22, 25, 30, 33]:
        dist = _BUS_DISTANCES[bus_id]
        lf = get_loss_factor(bus_id)
        print(f" Bus {bus_id:2d} | Distance from Bus 1: {dist:2d} hops | Cable Loss Factor: {lf:.3f} ({(lf-1)*100:.1f}% loss)")
