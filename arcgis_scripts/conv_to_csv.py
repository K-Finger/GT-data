import json
import pandas as pd

json_file = "data/data.json"
nodes_csv = "data/nodes.csv"
paths_csv = "data/paths.csv"

with open("./data.json", "r") as file:
    data = json.load(file)

node_ids = [node["id"] for node in data["nodes"]]

duplicates = set([id for id in node_ids if node_ids.count(id) > 1])

missing_ids = set(range(1, 945)) - set(node_ids)  # Assuming IDs should be 1-944

print(f"Total Nodes in JSON: {len(node_ids)}")
print(f"Duplicate IDs: {duplicates}")
print(f"Missing IDs: {missing_ids}")