from nobil.parser.extract import nobil_extract_data
from nobil.parser.annotate import write_annotated_nobil_csv
from bnetza.parser.rename import get_renamed_bnetza
from irve.extract import irve_extract_csv, write_annotated_irve_csv
from datex2.parser.parse_xml import parse_datex2_xml
from datex2.parser.restructure import restructure_datex2
from datex2.annotation.annotate import annotate_datex2
from pathlib import Path
import polars as pl
import json
import yaml

OUTPUT_PATH = "parsed"
RAW_PATH = "sources"


if Path(RAW_PATH).exists():
    sources = pl.read_csv(f"{RAW_PATH}/metadata.csv")
    datex2_sources = sources.filter(
        (pl.col("standard") == "DATEXII") | (pl.col("standard") == "DATEXII_P")
    )
    Path(OUTPUT_PATH).mkdir(exist_ok=True)

    other_sources = sources.select(pl.col("id"), pl.col("local")).rows()

    nobil_data = [
        s for s in other_sources if (s[1] is not None) and ("nobil" in s[1].lower())
    ]

    source_nobil = nobil_data[0][1]  # "20-01-2025-NOBIL-dump.json"
    name_nobil = nobil_data[0][0]

    irve_data = [
        s for s in other_sources if (s[1] is not None) and ("irve" in s[1].lower())
    ]

    source_irve = irve_data[0][1]
    name_irve = irve_data[0][0]

    nobil_data = nobil_extract_data(source_nobil)
    write_annotated_nobil_csv(nobil_data, OUTPUT_PATH, name_nobil, "nobil/metadata.yml")

    irve_data = irve_extract_csv(source_irve)
    write_annotated_irve_csv(irve_data, OUTPUT_PATH, name_irve, "irve/metadata.yml")

    get_renamed_bnetza(
        OUTPUT_PATH,
        "sources/BNETZA/bnetza_charging_stations_raw_08_2025.xlsx",
    )

    with open("datex2/annotations.yml", "r") as f:
        annotations = yaml.safe_load(f)
    for row in datex2_sources.rows(named=True):
        cc = row["id"].split("-")[0]
        if (row["local"] is not None) and ("xml" in row["local"].lower()):
            data = parse_datex2_xml(row["local"], country_code=cc)
        else:
            data = {}

        if len(data) != 0:
            restructured = restructure_datex2(data, row["id"])
            current_output_path = Path(f"{OUTPUT_PATH}/{row['id']}")
            current_output_path.mkdir(exist_ok=True, parents=True)

            descriptor = annotate_datex2(
                restructured, metadata=row, annotations=annotations
            )

            for name, dataframe in restructured.items():
                dataframe.write_csv(current_output_path.joinpath(f"{name}.csv"))

            with open(
                current_output_path.joinpath("datapackage.json"), "w", encoding="utf-8"
            ) as f:
                json.dump(descriptor, f, indent=4, ensure_ascii=False)
else:
    print(
        f"{RAW_PATH} does not exist, create it or run get_data.py to get the source files."
    )
