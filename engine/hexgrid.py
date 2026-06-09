"""Hex grid geometry for WoW Raiders (Heroes-style hex board).

Pure geometry, deterministic, no game state. Uses offset \"odd-r\" coordinates
(horizontal layout, odd rows pushed right) for human-friendly (col,row) board
labels, and converts to cube coordinates for distance / range math.

Reference: Red Blob Games hexagon guide.
"""
import heapq

# odd-r offset neighbour direction differences, indexed by [row parity][dir]
_ODDR_DIRS = [
    # even rows (parity 0)
    [(+1, 0), (0, -1), (-1, -1), (-1, 0), (-1, +1), (0, +1)],
    # odd rows (parity 1)
    [(+1, 0), (+1, -1), (0, -1), (-1, 0), (0, +1), (+1, +1)],
]


def oddr_to_cube(col, row):
    x = col - (row - (row & 1)) // 2
    z = row
    y = -x - z
    return (x, y, z)


def cube_distance(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))


def distance(a, b):
    """Hex distance between two (col,row) offset hexes."""
    return cube_distance(oddr_to_cube(*a), oddr_to_cube(*b))


def neighbors(hex_):
    col, row = hex_
    parity = row & 1
    return [(col + dc, row + dr) for dc, dr in _ODDR_DIRS[parity]]


def in_bounds(hex_, width, height):
    col, row = hex_
    return 0 <= col < width and 0 <= row < height


def neighbors_in_bounds(hex_, width, height):
    return [h for h in neighbors(hex_) if in_bounds(h, width, height)]


def hexes_in_range(center, radius):
    """All offset hexes within `radius` steps of center (BFS, no bounds)."""
    seen = {center}
    frontier = [center]
    for _ in range(radius):
        nxt = []
        for h in frontier:
            for n in neighbors(h):
                if n not in seen:
                    seen.add(n)
                    nxt.append(n)
        frontier = nxt
    return seen


def reachable(start, budget, width, height, enter_cost):
    """Dijkstra over hexes. `enter_cost(hex) -> int | None` is the cost to ENTER
    a hex (None = impassable). Returns dict hex -> min cost (<= budget).
    Start has cost 0 and its own enter cost is not charged.
    """
    dist = {start: 0}
    pq = [(0, start)]
    while pq:
        d, h = heapq.heappop(pq)
        if d > dist.get(h, float("inf")):
            continue
        for n in neighbors_in_bounds(h, width, height):
            c = enter_cost(n)
            if c is None:
                continue
            nd = d + c
            if nd <= budget and nd < dist.get(n, float("inf")):
                dist[n] = nd
                heapq.heappush(pq, (nd, n))
    return dist


def shortest_path(start, goal, width, height, enter_cost):
    """Dijkstra path start->goal as list of hexes (incl. start & goal), ignoring
    movement budget. Returns (path, total_cost) or (None, None) if unreachable.
    `enter_cost` is not charged for the start hex.
    """
    if start == goal:
        return [start], 0
    dist = {start: 0}
    prev = {}
    pq = [(0, start)]
    while pq:
        d, h = heapq.heappop(pq)
        if h == goal:
            break
        if d > dist.get(h, float("inf")):
            continue
        for n in neighbors_in_bounds(h, width, height):
            c = enter_cost(n)
            if c is None:
                continue
            nd = d + c
            if nd < dist.get(n, float("inf")):
                dist[n] = nd
                prev[n] = h
                heapq.heappush(pq, (nd, n))
    if goal not in dist:
        return None, None
    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    path.reverse()
    return path, dist[goal]


def cube_round(x, y, z):
    rx, ry, rz = round(x), round(y), round(z)
    dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return (rx, ry, rz)


def cube_to_oddr(cube):
    x, y, z = cube
    col = x + (z - (z & 1)) // 2
    return (col, z)


def line(a, b):
    """Hex line of offset hexes from a to b inclusive (cube interpolation)."""
    n = distance(a, b)
    ac = oddr_to_cube(*a)
    bc = oddr_to_cube(*b)
    out = []
    for i in range(n + 1):
        t = 0.0 if n == 0 else i / n
        x = ac[0] + (bc[0] - ac[0]) * t
        y = ac[1] + (bc[1] - ac[1]) * t
        z = ac[2] + (bc[2] - ac[2]) * t
        h = cube_to_oddr(cube_round(x, y, z))
        if not out or out[-1] != h:
            out.append(h)
    return out
