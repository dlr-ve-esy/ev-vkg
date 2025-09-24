from glob import glob
from parser.parse_xml import parse_datex2_xml
from parser.parse_json import parse_datex2_json
from parser.restructure import restructure_datex2
from annotation.annotate import annotate_datex2
from pathlib import Path
from typing import List
import polars as pl
import json
import yaml

paths: List[Path] = [Path(f) for f in glob("sources/XML/*")]

OUTPUT_BASE = "parsed"
sources = pl.read_csv("sources/metadata.csv")
datex2_sources = sources.filter(pl.col("standard") == "DATEXII")

with open("datex2/annotations.yml", "r") as f:
    annotations = yaml.safe_load(f)
for row in datex2_sources.rows(named=True):
    cc = row["id"].split("-")[0]
    if "xml" in row["local"].lower():
        data = parse_datex2_xml(row["local"], country_code=cc)
    # elif "json" in row["local"].lower():
    #     data = parse_datex2_json(row["local"], country_code=cc)
    else:
        data = {}

    if len(data) != 0:
        restructured = restructure_datex2(data, row["id"])
        output_path = Path(f"{OUTPUT_BASE}/{row['id']}")
        output_path.mkdir(exist_ok=True, parents=True)

        descriptor = annotate_datex2(
            restructured, metadata=row, annotations=annotations
        )

        for name, dataframe in restructured.items():
            dataframe.write_csv(output_path.joinpath(f"{name}.csv"))

        with open(output_path.joinpath("datapackage.json"), "w", encoding="utf-8") as f:
            json.dump(descriptor, f, indent=4, ensure_ascii=False)
