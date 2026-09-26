edges = [
    # Main spine
    ((24, 25), (24, 24)),
    ((24, 24), (24, 22)),
    ((24, 22), (24, 19)),
    ((24, 19), (24, 16)),
    ((24, 16), (24, 15)),
    ((24, 15), (24, 14)),
    ((24, 14), (24, 13)),
    # Horizontal relic cross
    ((16, 19), (20, 19)),
    ((20, 19), (24, 19)),
    ((24, 19), (28, 19)),
    ((28, 19), (32, 19)),
    # Top horizontal bridge
    ((21, 16), (24, 16)),
    ((24, 16), (27, 16)),
    # Outer diamond
    ((24, 22), (22, 21)),
    ((22, 21), (20, 19)),
    ((20, 19), (20, 17)),
    ((20, 17), (21, 16)),
    ((21, 16), (19, 14)),
    ((19, 14), (24, 13)),
    ((24, 22), (26, 21)),
    ((26, 21), (28, 19)),
    ((28, 19), (28, 17)),
    ((28, 17), (27, 16)),
    ((27, 16), (29, 14)),
    ((29, 14), (24, 13)),
    # Inner diamond
    ((24, 16), (21, 18)),
    ((21, 18), (24, 22)),
    ((24, 16), (27, 18)),
    ((27, 18), (24, 22)),
]

nodes = set()
for a, b in edges:
    nodes.add(a)
    nodes.add(b)

print(f"Total nodes in graph: {len(nodes)}")

# Build adjacency list
adj = {n: set() for n in nodes}
for a, b in edges:
    adj[a].add(b)
    adj[b].add(a)

# BFS to check connectivity
start = (24, 16)
visited = set([start])
queue = [start]
while queue:
    curr = queue.pop(0)
    for nxt in adj[curr]:
        if nxt not in visited:
            visited.add(nxt)
            queue.append(nxt)

print(f"Visited nodes from {start}: {len(visited)} / {len(nodes)}")
assert len(visited) == len(nodes), "Graph is not fully connected!"
print("Graph is 100% connected and bidirectional!")
