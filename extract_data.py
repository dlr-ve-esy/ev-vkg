"""Extract the parsed CSV outputs from the configured input snapshots.

Input selection is driven by ``run_config.yaml``: every dataset entry
records its stable dataset ID, input file, checksum, format and parsed
output directory. The extractor no longer hard-codes the BNetZA
workbook filename and no longer discovers inputs by filename
substrings; it dispatches on the configured format and verifies each
input against its recorded checksum before parsing.

Entries with an input file but no parsed directory (e.g. hu.1, whose
acquired XML produced no EVSE records in the published run) are
reported and skipped. Entries without an input file were not acquired
and are listed for transparency. Analysis inclusion is a separate
concern: excluded datasets with inputs (e.g. de.1) are still extracted
so the parsed output remains inspectable, while the notebook selects
analysis datasets from the same configuration.
"""

from pathlib import Path
import json

import polars as pl
import yaml

import run_config as rc
from bnetza.parser.rename import get_renamed_bnetza
from datex2.annotation.annotate import annotate_datex2
from datex2.parser.parse_json import parse_datex2_json
from datex2.parser.parse_xml import parse_datex2_xml
from datex2.parser.restructure import restructure_datex2
from irve.extract import irve_extract_csv, write_annotated_irve_csv
from nobil.parser.annotate import write_annotated_nobil_csv
from nobil.parser.extract import nobil_extract_data

OUTPUT_PATH = "parsed"
RAW_PATH = "sources"
DATEX2_ANNOTATIONS = "datex2/annotations.yml"


def metadata_records() -> dict[str, dict]:
    """Assessment records from sources/metadata.csv keyed by record id."""
    sources = pl.read_csv(f"{RAW_PATH}/metadata.csv")
    return {row["id"]: row for row in sources.iter_rows(named=True)}


def adapt_datex2_json_frames(data: dict) -> dict:
    """Map parse_datex2_json frames onto the parse_datex2_xml schema.

    The JSON parser was never wired into restructure_datex2 (its branch
    is commented out in datex2/main.py) and emits differently named
    frames: geolocations/evse/connections instead of the XML parser's
    locations/points/compatibilities, and address columns named
    street/postal_name/zip_code instead of
    street_dirty/city/postcode. The JSON evse frame also hangs off
    charging columns (stations) rather than facilities, so facility_id
    is joined in through the columns frame.
    """
    if "geolocations" in data:
        data["locations"] = data.pop("geolocations")

    if "evse" in data:
        evse = data.pop("evse")
        columns = data.pop("columns", None)
        if columns is not None:
            evse = evse.join(
                columns.select(
                    pl.col("id").alias("column_id"), pl.col("facility_id")
                ),
                on="column_id",
                how="left",
            )
        data["points"] = evse.select(pl.col("id"), pl.col("facility_id"))

    if "connections" in data:
        data["compatibilities"] = data.pop("connections").rename(
            {"evse_id": "point_id"}
        )

    if "addresses" in data:
        rename = {
            old: new
            for old, new in [
                ("street", "street_dirty"),
                ("postal_name", "city"),
                ("zip_code", "postcode"),
            ]
            if old in data["addresses"].columns
        }
        if rename:
            data["addresses"] = data["addresses"].rename(rename)

    return data


def extract_datex2(entry: rc.DatasetEntry, records: dict[str, dict], annotations: dict):
    """Parse a DATEX II publication (XML or JSON) into entry.parsed_dir."""
    path = entry.input_file.path
    if path.suffix.lower() == ".json":
        data = adapt_datex2_json_frames(
            parse_datex2_json(str(path), country_code=entry.country)
        )
    else:
        data = parse_datex2_xml(str(path), country_code=entry.country)

    if len(data) == 0:
        print(f"{entry.dataset_id}: no records parsed from {path}; skipped")
        return

    # The annotation descriptor carries the assessment record's
    # metadata; the record is selected by its recorded id, never by
    # date-substring matching.
    row = records.get(entry.snapshot_id)
    if row is None:
        raise KeyError(
            f"{entry.dataset_id}: no metadata record with id "
            f"{entry.snapshot_id!r} in {RAW_PATH}/metadata.csv"
        )

    restructured = restructure_datex2(data, row["id"])
    output_dir = Path(OUTPUT_PATH) / entry.parsed_dir
    output_dir.mkdir(exist_ok=True, parents=True)

    descriptor = annotate_datex2(restructured, metadata=row, annotations=annotations)
    for name, dataframe in restructured.items():
        dataframe.write_csv(output_dir.joinpath(f"{name}.csv"))
    with open(
        output_dir.joinpath("datapackage.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(descriptor, f, indent=4, ensure_ascii=False)
    print(f"{entry.dataset_id}: parsed into {output_dir}")


def main() -> None:
    config = rc.load()

    if not Path(RAW_PATH, "metadata.csv").exists():
        print(
            f"{RAW_PATH}/metadata.csv does not exist; create it or run "
            "get_data.py to get the source files."
        )
        return

    records = metadata_records()
    with open(DATEX2_ANNOTATIONS, "r") as f:
        annotations = yaml.safe_load(f)

    Path(OUTPUT_PATH).mkdir(exist_ok=True)

    for entry in config.datasets:
        if entry.input_file is None:
            print(f"{entry.dataset_id}: no input recorded; not extracted")
            continue
        if entry.parsed_dir is None:
            print(
                f"{entry.dataset_id}: input {entry.input_file.path} recorded "
                "but no parsed_dir; not extracted (see exclusion_reason "
                "in run_config.yaml)"
            )
            continue
        if not entry.input_file.path.exists():
            raise FileNotFoundError(
                f"{entry.dataset_id}: configured input {entry.input_file.path} "
                "does not exist; run get_data.py or fix run_config.yaml"
            )
        if not entry.input_file.verify():
            raise ValueError(
                f"{entry.dataset_id}: checksum mismatch for "
                f"{entry.input_file.path}; the file does not match the "
                "snapshot recorded in run_config.yaml"
            )

        if entry.format == "datex2":
            extract_datex2(entry, records, annotations)
        elif entry.format == "nobil":
            data = nobil_extract_data(str(entry.input_file.path))
            write_annotated_nobil_csv(
                data, OUTPUT_PATH, entry.parsed_dir, "nobil/metadata.yml"
            )
            print(f"{entry.dataset_id}: parsed into {OUTPUT_PATH}/{entry.parsed_dir}")
        elif entry.format == "irve":
            data = irve_extract_csv(str(entry.input_file.path))
            write_annotated_irve_csv(
                data, OUTPUT_PATH, entry.parsed_dir, "irve/metadata.yml"
            )
            print(f"{entry.dataset_id}: parsed into {OUTPUT_PATH}/{entry.parsed_dir}")
        elif entry.format == "bnetza":
            # The parser names its output directory after the content
            # date of the workbook (DE-<yyyymmdd>-BNETZA-BNETZA); check
            # it against the parsed_dir recorded in the configuration.
            get_renamed_bnetza(OUTPUT_PATH, str(entry.input_file.path))
            expected = Path(OUTPUT_PATH) / entry.parsed_dir
            if expected.exists():
                print(f"{entry.dataset_id}: parsed into {expected}")
            else:
                print(
                    f"{entry.dataset_id}: WARNING parser did not produce "
                    f"{expected}; the workbook content date does not match "
                    "the snapshot recorded in run_config.yaml"
                )
        else:
            print(
                f"{entry.dataset_id}: format {entry.format!r} has no "
                "extraction pipeline; skipped"
            )


if __name__ == "__main__":
    main()
