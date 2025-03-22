import ast
import sys

nodes = []
node_id = 1
coord_map = {}
paths = []
REQUIRED_KEYS = ['BUILDING_NAME', 'X', 'Y']

def load_arcgis_data():
    try:
        with open("data/arcgis_export_raw.txt", "r", encoding="utf-8") as file:
            data = file.read()
            data = ast.literal_eval(data)
            
            if isinstance(data, list):
                return data
            else:
                raise ValueError("Raw data is not a list.")
                
    except (SyntaxError, ValueError) as e:
        sys.exit(f"Error loading raw data: {e}")
    except FileNotFoundError:
        sys.exit("Error loading raw data: The file was not found.")
    except Exception as e:
        sys.exit(f"Error loading raw data: An unexpected error occurred: {e}")

def add_node(raw_node: dict): 
    global node_id

    missing_keys = [key for key in REQUIRED_KEYS if key not in raw_node]
    if missing_keys:
        sys.exit(f"Error: Node ID {node_id}, ORDER {raw_node.get('ORDER', 'Unknown')} is missing the following attributes: {', '.join(missing_keys)}. Exiting Script.")

    nodes.append({
        "id": node_id,
        "building_name": raw_node['BUILDING_NAME'],
        "x": raw_node['X'],
        "y": raw_node['Y']
    })
    coord_map[(raw_node['X'], raw_node['Y'])] = node_id

    sequence = get_sequence(raw_node)
    if sequence == "First":
        connect_path(node_id, node_id + 1)
    elif sequence == "Middle":
        connect_path(node_id - 1, node_id)
        connect_path(node_id, node_id + 1)
    elif sequence == "Last":
        connect_path(node_id - 1, node_id)

    node_id += 1

def get_sequence(raw_node: dict):
    vertex_order = raw_node['VERTEX_ORDER']
    part_size = raw_node["PART_SIZE"]

    if vertex_order == 1:
        return "First"
    elif vertex_order == part_size:
        return "Middle"
    else:
        return "Last"

def connect_path(node_id1, node_id2):
    paths.append({"from": node_id1, "to": node_id2})
    paths.append({"from": node_id2, "to": node_id1})

# Main logic
arcgis_export_raw = load_arcgis_data()

for raw_node in arcgis_export_raw:
    order = raw_node['ORDER']
    x, y = raw_node['X'], raw_node['Y']
    
    if (x, y) in coord_map:
        existing_node = coord_map[(x, y)]
        sequence = get_sequence(raw_node)
        if sequence == "First":
            connect_path(existing_node, node_id)
        elif sequence == "Middle":
            connect_path(existing_node, node_id - 1)
            connect_path(existing_node, node_id)
        elif sequence == "Last":
            connect_path(existing_node, node_id - 1)
    else:
        add_node(raw_node)

# Save the data to a file
import json

data = {"nodes": nodes, "paths": paths}

# Convert the data to a JSON string
data_json = json.dumps(data, indent=4)

# Write the JSON string to data.txt
with open("data/data.txt", "w", encoding="utf-8") as file:
    file.write(data_json)