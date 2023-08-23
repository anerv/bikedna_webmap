import geopandas as gpd
import yaml
import pickle
from src import db_functions as dbf


with open(r"../config.yml") as file:
    parsed_yaml_file = yaml.load(file, Loader=yaml.FullLoader)

    crs = parsed_yaml_file["CRS"]

    study_area = parsed_yaml_file["study_area"]

    db_name = parsed_yaml_file["db_name"]
    db_user = parsed_yaml_file["db_user"]
    db_password = parsed_yaml_file["db_password"]
    db_host = parsed_yaml_file["db_host"]
    db_port = parsed_yaml_file["db_port"]

print("Settings loaded!")

# filepaths
osm_data_fp = f"../data/osm/{study_area}/processed/"
osm_results_fp = f"../results/osm/{study_area}/data/"

geodk_data_fp = f"../data/reference/{study_area}/processed/"
geodk_results_fp = f"../results/reference/{study_area}/data/"

compare_results_fp = f"../results/compare/{study_area}/data/"


# read data

osm_simplified_edges = gpd.read_parquet(osm_data_fp + "osm_edges_simplified.parquet")

geodk_simplified_edges = gpd.read_parquet(
    geodk_data_fp + "ref_edges_simplified.parquet"
)

osm_component_edges = gpd.read_parquet(
    osm_results_fp + "osm_edges_component_id.parquet"
)
geodk_component_edges = gpd.read_parquet(
    geodk_results_fp + "ref_edges_component_id.parquet"
)

osm_largest_cc = gpd.read_parquet(
    osm_results_fp + "largest_connected_component.parquet"
)
geodk_largest_cc = gpd.read_parquet(
    geodk_results_fp + "largest_connected_component.parquet"
)

buffer_dist = 15
hausdorff_dist = 17
angle = 30

osm_matched = gpd.read_parquet(
    compare_results_fp
    + f"osm_matched_segments_{buffer_dist}_{hausdorff_dist}_{angle}.parquet"
)
geodk_matched = gpd.read_parquet(
    compare_results_fp
    + f"ref_matched_segments_{buffer_dist}_{hausdorff_dist}_{angle}.parquet"
)

osm_unmatched = gpd.read_parquet(
    compare_results_fp
    + f"osm_unmatched_segments_{buffer_dist}_{hausdorff_dist}_{angle}.parquet"
)
geodk_unmatched = gpd.read_parquet(
    compare_results_fp
    + f"ref_unmatched_segments_{buffer_dist}_{hausdorff_dist}_{angle}.parquet"
)

with open(compare_results_fp + "grid_results_extrinsic.pickle", "rb") as fp:
    extrinsic_grid = pickle.load(fp)

with open(osm_results_fp + "grid_results_intrinsic.pickle", "rb") as fp:
    osm_intrinsic_grid = pickle.load(fp)


# join edge data

ref_cols = [
    "edge_id",
    "length",
    "infrastructure_length",
    "protected",
    "from",
    "to",
    "component",
    "geometry",
]

osm_cols = [
    "edge_id",
    "length",
    "infrastructure_length",
    "protected",
    "bicycle_infrastructure",
    "bicycle_bidirectional",
    "bicycle_geometries",
    "component",
    "geometry",
]


osm_joined_edges = osm_simplified_edges.merge(
    osm_component_edges[["edge_id", "component"]], on="edge_id"
)

assert len(osm_joined_edges) == len(osm_simplified_edges)

osm_joined_edges = osm_joined_edges[osm_cols]

osm_joined_edges["largest_cc"] = False

osm_joined_edges.loc[osm_joined_edges.component == 0, "largest_cc"] = True

assert len(osm_joined_edges[osm_joined_edges.largest_cc == True]) == len(osm_largest_cc)


geodk_joined_edges = geodk_simplified_edges.merge(
    geodk_component_edges[["edge_id", "component"]], on="edge_id"
)

assert len(geodk_joined_edges) == len(geodk_simplified_edges)

geodk_joined_edges = geodk_joined_edges[ref_cols]

geodk_joined_edges["largest_cc"] = False

geodk_joined_edges.loc[geodk_joined_edges.component == 25, "largest_cc"] = True

assert len(geodk_joined_edges[geodk_joined_edges.largest_cc == True]) == len(
    geodk_largest_cc
)


data = [
    osm_joined_edges,
    geodk_joined_edges,
    osm_matched,
    osm_unmatched,
    geodk_matched,
    geodk_unmatched,
    extrinsic_grid,
    osm_intrinsic_grid,
]
table_names = [
    "osm_edges",
    "geodk_edges",
    "osm_matched",
    "osm_unmatched",
    "geodk_matched",
    "geodk_unmatched",
    "extrinsic_grid",
    "osm_intrinsic_grid",
]

connection = dbf.connect_pg(db_name, db_user, db_password)

engine = dbf.connect_alc(db_name, db_user, db_password, db_port=db_port)

for name, dataset in zip(table_names, data):
    dbf.to_postgis(geodataframe=dataset, table_name=name, engine=engine)

q1 = "SELECT edge_id, infrastructure_length, component FROM osm_edges LIMIT 10;"
q2 = "SELECT edge_id, infrastructure_length, component FROM geodk_edges LIMIT 10;"

test1 = dbf.run_query_pg(q1, connection)

print(test1)

test2 = dbf.run_query_pg(q2, connection)

print(test2)

connection.close()
