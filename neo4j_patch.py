"""
GopherTunnels — Neo4j Patch Tool
=================================
Patches Neo4j Building nodes from the latest buildings JSON in data/graphs/.

Usage:
    python data/neo4j_patch.py

Source file is auto-detected as the most recently modified buildings*.json
in data/graphs/. Edit that file, then run this tool to push changes to Neo4j.

Neo4j is the source of truth at runtime. This tool only patches specific
fields — it never overwrites hours, visits, address, or other DB-managed data.
"""

import glob
import json
import os
import sys

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# ── Source file ───────────────────────────────────────────────────────────────

def find_buildings_file() -> str:
    """Auto-detect the most recently modified buildings*.json in data/graphs/."""
    pattern = os.path.join("data", "graphs", "buildings*.json")
    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(f"No buildings*.json found in data/graphs/")
    return max(matches, key=os.path.getmtime)


def load_buildings(path: str) -> list[dict]:
    with open(path, "r") as f:
        data = json.load(f)
    return [
        node for node in data["nodes"]
        if node.get("type") == "building" and node.get("building_name")
    ]


# ── Neo4j connection ──────────────────────────────────────────────────────────

def get_driver():
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    if not all([uri, username, password]):
        print("ERROR: Missing NEO4J_URI, NEO4J_USERNAME, or NEO4J_PASSWORD in .env")
        sys.exit(1)
    return GraphDatabase.driver(uri, auth=(username, password))


# ── Patch functions ───────────────────────────────────────────────────────────

def patch_entrance_nodes(session, buildings: list[dict]):
    """Push entrance_nodes arrays to Building nodes."""
    print("\n[Entrance Nodes]")
    targets = [b for b in buildings if b.get("entrance_nodes")]
    if not targets:
        print("  No buildings with entrance_nodes found in source file.")
        return

    updated, not_found = 0, 0
    for b in targets:
        result = session.run(
            """
            MATCH (n:Building {building_name: $name})
            SET n.entrance_nodes = $entrance_nodes
            REMOVE n.entrance_points
            RETURN n.building_name AS name
            """,
            name=b["building_name"],
            entrance_nodes=json.dumps(b["entrance_nodes"]),
        )
        record = result.single()
        if record:
            print(f"  Updated:   {record['name']}")
            updated += 1
        else:
            print(f"  NOT FOUND: {b['building_name']}")
            not_found += 1

    print(f"  — {updated} updated, {not_found} not found")


def patch_positions(session, buildings: list[dict]):
    """Update lat/lon on Building nodes."""
    print("\n[Positions]")
    targets = [b for b in buildings if b.get("lat") is not None and b.get("lon") is not None]
    if not targets:
        print("  No buildings with lat/lon found in source file.")
        return

    updated, not_found = 0, 0
    for b in targets:
        result = session.run(
            """
            MATCH (n:Building {building_name: $name})
            SET n.latitude = $lat, n.longitude = $lon
            RETURN n.building_name AS name
            """,
            name=b["building_name"],
            lat=b["lat"],
            lon=b["lon"],
        )
        record = result.single()
        if record:
            print(f"  Updated:   {record['name']}")
            updated += 1
        else:
            print(f"  NOT FOUND: {b['building_name']}")
            not_found += 1

    print(f"  — {updated} updated, {not_found} not found")


def patch_disconnected(session, buildings: list[dict]):
    """Add :TunnelBuilding label to connected buildings, remove from disconnected ones."""
    print("\n[TunnelBuilding Labels]")
    updated, not_found = 0, 0
    for b in buildings:
        is_disconnected = b.get("disconnected", False)
        # Connected buildings get :TunnelBuilding label; disconnected ones don't
        query = (
            "MATCH (n:Building {building_name: $name}) REMOVE n:TunnelBuilding RETURN n.building_name AS name"
            if is_disconnected else
            "MATCH (n:Building {building_name: $name}) SET n:TunnelBuilding RETURN n.building_name AS name"
        )
        result = session.run(query, name=b["building_name"])
        record = result.single()
        if record:
            flag = "disconnected" if is_disconnected else "tunnel    "
            print(f"  [{flag}] {record['name']}")
            updated += 1
        else:
            print(f"  NOT FOUND: {b['building_name']}")
            not_found += 1

    print(f"  — {updated} updated, {not_found} not found")


# ── Menu ──────────────────────────────────────────────────────────────────────

PATCHES = {
    "1": ("Entrance nodes  — push entrance_nodes array to Building nodes", patch_entrance_nodes),
    "2": ("Positions       — update lat/lon on Building nodes",            patch_positions),
    "3": ("Disconnected    — set/clear disconnected flag on Building nodes", patch_disconnected),
}


def run_menu():
    source_path = find_buildings_file()
    buildings = load_buildings(source_path)

    with_entrances = sum(1 for b in buildings if b.get("entrance_nodes"))
    disconnected   = sum(1 for b in buildings if b.get("disconnected"))

    print("\nGopherTunnels Neo4j Patch Tool")
    print("=" * 40)
    print(f"Source: {source_path}")
    print(f"  {len(buildings)} buildings | {with_entrances} with entrance_nodes | {disconnected} disconnected")

    while True:
        print("\nSelect patch to apply:")
        for key, (label, _) in PATCHES.items():
            print(f"  {key}. {label}")
        print("  4. All  — run all patches above")
        print("  0. Exit")

        choice = input("\n> ").strip()

        if choice == "0":
            print("Bye.")
            break

        if choice not in ("1", "2", "3", "4"):
            print("Invalid choice.")
            continue

        confirm = input("Apply patch? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            continue

        driver = get_driver()
        driver.verify_connectivity()
        with driver.session() as session:
            if choice == "4":
                for _, (_, fn) in PATCHES.items():
                    fn(session, buildings)
            else:
                _, fn = PATCHES[choice]
                fn(session, buildings)
        driver.close()


if __name__ == "__main__":
    run_menu()
