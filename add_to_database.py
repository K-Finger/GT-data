import json
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

DATA_PATH = "./data/data.json"

with open(DATA_PATH, "r") as file:
    data = json.load(file)

def create_nodes(tx, nodes):
    for node in nodes:
        print(f"Adding node {node['id']}...")
        tx.run("""
            MERGE (n:Node {id: $id})
            SET n += $props
        """, id=node["id"], props={k: v for k, v in node.items() if k != "id"})

def create_relationships(tx, paths):
    for path in paths:
        print(f"Creating relationship: {path['from']} <--> {path['to']}")
        tx.run("""
            MATCH (a:Node {id: $from_id}), (b:Node {id: $to_id})
            MERGE (a)-[:CONNECTED_TO]->(b)
            MERGE (b)-[:CONNECTED_TO]->(a)
        """, from_id=int(path["from"]), to_id=int(path["to"]))

with GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD)) as driver:
    driver.verify_connectivity()
    
    with driver.session() as session:
        session.execute_write(create_nodes, data["nodes"]) 
        session.execute_write(create_relationships, data["paths"])
    
    print("Nodes and Relationships added successfully!")
