'''
import arcpy

DEFAULT_PATH = r"~\ArcGIS\Projects\GopherWayARCGIS\Default.gdb"
NODES = [] 

feature_class = "Gopher_Way_Route"

# DEFINE WGS 1984 (long, lat) as spatial reference
wgs84 = arcpy.SpatialReference(4326)  # EPSG:4326
# Get the spatial reference of the input feature class
input_spatial_ref = arcpy.Describe(feature_class).spatialReference

order = 1  

fields = ["OID@", "SHAPE@", "SITE_BUILDING_FLOOR", "BLDG_NAME_LABEL"]

for feature in arcpy.da.SearchCursor(feature_class, fields):
    feature_id = feature[0]
    geometry = feature[1]
    site_building_floor = feature[2]
    building_name = feature[3]

    if input_spatial_ref.factoryCode != 4326:  # If not already WGS 1984
        geometry = geometry.projectAs(wgs84)
        
    part_index = 1

    for part in geometry:
        vertex_order = 1  # Reset vertex order for each part
        for vertex in part:
            node_entry = {
                "ORDER": order,
                "SITE_BUILDING_FLOOR": site_building_floor,
                "BUILDING_NAME": building_name,
                "OBJECT_ID": feature_id,
                "PART": part_index,
                "PART_SIZE": len(part),
                "VERTEX_ORDER": vertex_order,  # Order within the part
                "X": vertex.X,
                "Y": vertex.Y
            }
            NODES.append(node_entry)
            order += 1 
            vertex_order += 1  # Increment vertex order within the part

        part_index += 1 

print(NODES)
'''