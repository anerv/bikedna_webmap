# %%

import geopandas as gpd
import yaml
import pickle
from src import db_functions as dbf

# %%
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
# %%
# filepaths
osm_data_fp = f"../data/osm/{study_area}/processed/"
osm_results_fp = f"../results/osm/{study_area}/data/"

geodk_data_fp = f"../data/reference/{study_area}/processed/"
geodk_results_fp = f"../results/reference/{study_area}/data/"

compare_results_fp = f"../results/compare/{study_area}/data/"

# %%
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

# %%
with open(compare_results_fp + "grid_results_extrinsic.pickle", "rb") as fp:
    extrinsic_grid = pickle.load(fp)

with open(osm_results_fp + "grid_results_intrinsic.pickle", "rb") as fp:
    osm_intrinsic_grid = pickle.load(fp)

# %%
# TODO: join edges with comp and largest cc (or make sure largest cc is 0/1)
# %%

# TODO: subset all data

ref_cols = [
    "edge_id",
    "length",
    "infrastructure_length",
    "protected",
    "from",
    "to",
    "geometry",
]

# %%
osm_cols = [
    "edge_id",
    "length",
    "infrastructure_length",
    "protected",
    "bicycle_infrastructure",
    "bicycle_bidirectional",
    "bicycle_geometries",
    "geometry",
]


# %%


geodk = gpd.read_file(geodk_fp)

geodk.columns = geodk.columns.str.lower()

useful_cols = [
    "fot_id",
    "mob_id",
    "feat_kode",
    "feat_type",
    "featstatus",
    "geomstatus",
    "startknude",
    "slutknude",
    "niveau",
    "overflade",
    "rund_koer",
    "kom_kode",
    "vejkode",
    "tilfra_koe",
    "trafikart",
    "vejklasse",
    "vej_mynd",
    "vej_type",
    "geometry",
]

geodk = geodk[useful_cols]

geodk = geodk.to_crs(crs)

assert geodk.crs == crs

assert len(geodk) == len(geodk[geodk_id_col].unique())

# %%
# Get cycling infrastructure
geodk_bike = geodk.loc[
    geodk.vejklasse.isin(["Cykelsti langs vej", "Cykelbane langs vej"])
].copy()

# Create unique edge id column
geodk_bike["edge_id"] = geodk_bike.fot_id

assert len(geodk_bike.edge_id) == len(geodk_bike)
# %%
connection = dbf.connect_pg(db_name, db_user, db_password)

engine = dbf.connect_alc(db_name, db_user, db_password, db_port=db_port)

dbf.to_postgis(geodataframe=geodk_bike, table_name="geodk_bike", engine=engine)

q = "SELECT edge_id, vejklasse FROM geodk_bike LIMIT 10;"

test = dbf.run_query_pg(q, connection)

print(test)

connection.close()

# %%
