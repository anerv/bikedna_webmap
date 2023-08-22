# %%

import os
import yaml
import shutil

with open(r"config.yml") as file:
    parsed_yaml_file = yaml.load(file, Loader=yaml.FullLoader)

    study_area = parsed_yaml_file["study_area"]

# Filepaths with the data and results from running BikeDNA
source_data = "/Users/anev/Dropbox/ITU/repositories/bikedna_big/data/"
source_results = "/Users/anev/Dropbox/ITU/repositories/bikedna_big/results/"

# %%
# copy all data and results to this repo

sources = [source_data, source_results]

destination_data = "data/"
destination_results = "results/"

destinations = [destination_data, destination_results]

for src, dst in zip(sources, destinations):
    shutil.copytree(src, dst, dirs_exist_ok=True)
    print(f"Successfully copied data from {src} to {dst}")

folder_names = os.listdir("data/")
folder_names = ["data/" + f for f in folder_names]

for f in folder_names:
    os.rename(f, f.lower())

folder_names = os.listdir("results/")
folder_names = ["results/" + f for f in folder_names]

for f in folder_names:
    os.rename(f, f.lower())

# %%
# remove maps and plots
res_type = ["compare", "osm", "reference"]

folder_type = ["maps_interactive", "maps_static", "plots"]

for res in res_type:
    for folder in folder_type:
        res_fp = f"results/{res}/{study_area}/{folder}/"

        shutil.rmtree(res_fp)

# %%
