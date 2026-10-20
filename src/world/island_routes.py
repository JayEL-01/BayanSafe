"""Campaign wayfinding data for the illustrated Mount Talon island map."""
from collections import deque

from src.utils.data_loader import load_json


def shortest_route(route_data, start, destination):
    """Return stop ids and normalized map points along the shortest marked road."""
    stops = route_data["stops"]
    if start not in stops or destination not in stops:
        return [], []
    if start == destination:
        return [start], [tuple(stops[start]["point"])]

    edges = route_data["connections"]
    parents = {start: None}
    parent_edges = {}
    pending = deque([start])
    while pending and destination not in parents:
        current = pending.popleft()
        for edge in edges:
            a, b = edge["from"], edge["to"]
            neighbor = b if a == current else a if b == current else None
            if neighbor is None or neighbor in parents:
                continue
            parents[neighbor] = current
            parent_edges[neighbor] = edge
            pending.append(neighbor)

    if destination not in parents:
        return [], []

    stop_ids = [destination]
    while stop_ids[-1] != start:
        stop_ids.append(parents[stop_ids[-1]])
    stop_ids.reverse()

    points = []
    for a, b in zip(stop_ids, stop_ids[1:]):
        edge = parent_edges[b]
        edge_points = [tuple(point) for point in edge["path"]]
        if edge["from"] != a:
            edge_points.reverse()
        points.extend(edge_points if not points else edge_points[1:])
    return stop_ids, points


def campaign_route_for_region(route_data, region):
    """Get the current and next story stops for a campaign region."""
    current = route_data["region_stops"].get(region)
    route = route_data["campaign_route"]
    if current not in route:
        return current, None, [current] if current else [], []
    index = route.index(current)
    destination = route[index + 1] if index + 1 < len(route) else None
    if destination is None:
        return current, None, [current], [tuple(route_data["stops"][current]["point"])]
    stops, points = shortest_route(route_data, current, destination)
    return current, destination, stops, points


def load_island_routes():
    return load_json("data/island_routes.json")
