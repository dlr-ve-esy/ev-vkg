from copy import deepcopy
from typing import OrderedDict
from typing import Any
from typing import Dict
from pathlib import Path
import polars as pl
from zlib import crc32
import string
import yaml
import frictionless as fl
import json


def irve_extract_csv(filepath: str):
    # Load and clean data
    data = pl.read_csv(
        filepath,
        infer_schema_length=None,
        null_values=["Non concerné", "inconnu", "non concerne"],
    ).unique()

    # Column mappings
    owner_columns = {
        "contact_amenageur": "contact",
        "siren_amenageur": "siren_code",
    }

    operator_columns = {
        "contact_operateur": "contact_b",
        "telephone_operateur": "phone",
    }

    geo_name_mapping = {
        "adresse_station": "street",
        "consolidated_longitude": "longitude",
        "consolidated_latitude": "latitude",
        "consolidated_code_postal": "zip_code",
        "consolidated_commune": "postal_name",
    }

    evse_information = [
        "id_pdc_itinerance",
        "id_pdc_local",
        "puissance_nominale",
        "prise_type_ef",
        "prise_type_2",
        "prise_type_combo_ccs",
        "prise_type_chademo",
        "prise_type_autre",
        "gratuit",
        "paiement_acte",
        "paiement_cb",
        "paiement_autre",
        "tarification",
    ]

    facility_designators = [
        "address_id",
        "nom_enseigne",
        "nom_station",
        "implantation_station",
    ]

    column_designators = [
        "id_station_itinerance",
        "id_station_local",
        "horaires",
        "created_at",
        "date_mise_en_service",
        "raccordement",
        "num_pdl",
        "nbre_pdc",
        "condition_acces",
    ]
    station_information = [
        "nom_enseigne",
        "id_station_itinerance",
        "id_station_local",
        "nom_station",
        "implantation_station",
        "horaires",
        "created_at",
        "date_mise_en_service",
        "raccordement",
        "nbre_pdc",
        "num_pdl",
        "condition_acces",
    ]
    data = data.with_columns(
        pl.col("id_station_itinerance").str.strip_chars(),
        pl.col("id_station_local").str.strip_chars(),
        pl.col("id_pdc_itinerance").str.strip_chars(),
        pl.col("id_pdc_local").str.strip_chars(),
    ).with_columns(
        pl.when(pl.col("id_pdc_itinerance").str.contains("/"))
        .then(
            pl.col("id_pdc_itinerance").str.split(by="/").list.last().str.strip_chars()
        )
        .when(pl.col("id_pdc_itinerance").str.contains(","))
        .then(
            pl.col("id_pdc_itinerance").str.split(by=",").list.last().str.strip_chars()
        )
        .otherwise(pl.col("id_pdc_itinerance")),
        pl.when(pl.col("id_pdc_local").str.contains("/"))
        .then(pl.col("id_pdc_local").str.split(by="/").list.last().str.strip_chars())
        .when(pl.col("id_pdc_local").str.contains(","))
        .then(pl.col("id_pdc_local").str.split(by=",").list.last().str.strip_chars())
        .otherwise(pl.col("id_pdc_local")),
    )
    # Process operator and owner columns
    data = (
        data.with_columns(
            pl.when(~pl.col("nom_operateur").is_null())
            .then(pl.col("nom_operateur"))
            .otherwise(pl.col("nom_amenageur"))
            .fill_null(pl.col("nom_enseigne"))
            .alias("operator")
        )
        .rename(operator_columns)
        .rename(owner_columns)
        .with_columns(pl.col("contact").fill_null(pl.col("contact_b")))
    )

    # Note: Some operators have multiple contacts and siren codes, this makes everything way too complex, not within scope
    # but it is an interesting excercise to create the graph associating entities with their codes!
    agents = (
        data.select(["operator"])
        .unique()
        .with_row_index()
        .with_columns(
            pl.col("index").map_elements(
                lambda x: f"IRVE_AGENT_{str(x).zfill(8)}", return_dtype=pl.String
            )
        )
        .rename({"index": "id"})
    )
    # Join agents with data
    data = data.join(
        agents.select(["id", "operator"]),
        on=["operator"],
        how="left",
        nulls_equal=True,
    ).rename({"id": "operator_id"})

    # Process geographic data
    data = data.rename(geo_name_mapping)
    data = data.with_columns(pl.col("street").str.strip_chars())
    geo_df = (
        data.select(geo_name_mapping.values())
        .unique()
        .with_columns(
            pl.struct("street", "zip_code", "postal_name")
            .map_elements(
                lambda row: int(
                    crc32(
                        "".join(
                            [
                                row["street"],
                                str(row["zip_code"]).replace("nulls", ""),
                                str(row["postal_name"]).replace("null", ""),
                            ]
                        ).encode("utf8")
                    )
                ),
                return_dtype=pl.Int64,
            )
            .alias("address_id"),
            pl.struct("longitude", "latitude")
            .map_elements(
                lambda row: int(
                    str(int(row["longitude"] * 100000)).replace("-", "1")
                    + str(int(row["latitude"] * 100000)).replace("-", "1")
                ),
                return_dtype=pl.Int64,
            )
            .alias("spatial_id"),
        )
    )

    # Join geographic data with main data
    data = data.join(
        geo_df,
        left_on=list(geo_name_mapping.values()),
        right_on=list(geo_name_mapping.values()),
        how="left",
        nulls_equal=True,
    ).with_columns(
        pl.struct("id_station_itinerance", "id_station_local")
        .map_elements(
            lambda row: row["id_station_itinerance"]
            if row["id_station_itinerance"] is not None
            else row["id_station_local"],
            return_dtype=pl.String,
        )
        .alias("id_facilitycol")
    )

    # Process facility designations
    facility_designation = data.select(
        ["id_facilitycol"] + facility_designators
    ).unique()

    facility_designation_dirty = facility_designation.filter(
        ~pl.col("id_facilitycol").is_unique()
    )
    facility_designation_null = facility_designation_dirty.filter(
        pl.col("id_facilitycol").is_null()
    )
    facility_designation_nnull = facility_designation_dirty.filter(
        ~pl.col("id_facilitycol").is_null()
    )

    suffixes = [""] + list(string.ascii_uppercase)

    facility_designation_filled = (
        facility_designation_null.with_row_index()
        .with_columns(
            pl.col("index")
            .map_elements(
                lambda row: f"IRVENA{str(row).zfill(6)}",
                return_dtype=pl.String,
            )
            .alias("id_facilitycol")
        )
        .drop("index")
    )

    facilitycol_complement = pl.concat(
        [
            facility_designation_nnull,
            facility_designation_filled,
        ]
    ).unique(subset=facility_designators)

    data = (
        data.join(
            facilitycol_complement.select(["id_facilitycol"] + facility_designators),
            on=facility_designators,
            how="left",
            nulls_equal=True,
        )
        .with_columns(
            pl.col("id_facilitycol_right").fill_null(pl.col("id_facilitycol"))
        )
        .drop("id_facilitycol")
        .rename({"id_facilitycol_right": "id_facilitycol"})
    )

    # Process facility columns
    facility_cols = (
        data.select(
            ["address_id", "spatial_id", "id_facilitycol"] + station_information
        )
        .unique()
        .with_columns(
            pl.when(pl.struct(["id_facilitycol"]).is_unique())
            .then(pl.col("id_facilitycol"))
            .otherwise(None)
            .alias("column_id_pre1"),
            pl.when(pl.struct(["id_facilitycol"] + facility_designators).is_unique())
            .then(pl.col("id_facilitycol") + "F")
            .otherwise(pl.col("id_facilitycol"))
            .alias("facility_id"),
            pl.col("id_facilitycol")
            .cum_count()
            .over("id_facilitycol")
            .alias("_dup_count"),
        )
    )

    facility_cols = (
        facility_cols.with_columns(
            pl.struct("id_facilitycol", "_dup_count")
            .map_elements(
                lambda row: f"{row['id_facilitycol']}C{suffixes[row['_dup_count']]}"
                if row["_dup_count"] < len(suffixes)
                else f"{row['id_facilitycol']}C{row['_dup_count']}",
                return_dtype=pl.String,
            )
            .alias("column_id_pre2")
        )
        .drop("_dup_count")
        .with_columns(
            pl.col("column_id_pre1")
            .fill_null(pl.col("column_id_pre2"))
            .alias("column_id"),
            pl.col("facility_id")
            .cum_count()
            .over("id_facilitycol")
            .alias("_dup_count"),
        )
    )

    non_unique_ids = (
        facility_cols.select(["facility_id"] + facility_designators)
        .unique()
        .filter(~pl.col("facility_id").is_unique())
    )["facility_id"].to_list()

    facility_cols = facility_cols.with_columns(
        pl.when(pl.col("facility_id").is_in(non_unique_ids))
        .then(
            pl.struct("facility_id", "_dup_count").map_elements(
                lambda row: f"{row['facility_id']}C{suffixes[row['_dup_count']]}"
                if row["_dup_count"] < len(suffixes)
                else f"{row['facility_id']}C{row['_dup_count']}",
                return_dtype=pl.String,
            )
        )
        .otherwise(pl.col("facility_id"))
    ).drop("_dup_count")

    facility_cols_df = (
        facility_cols.select(
            ["address_id", "spatial_id", "facility_id", "column_id"]
            + station_information
        )
        .with_columns(
            pl.struct("spatial_id", "address_id")
            .is_unique()
            .alias("coord_points_column"),
            pl.col("address_id")
            .is_unique()
            .not_()
            .alias("facility_has_multiple_columns"),
        )
        .with_columns(
            pl.col("facility_has_multiple_columns")
            .or_(pl.struct("spatial_id", "address_id").is_unique().not_())
            .alias("coord_points_facility")
        )
    )

    data = data.join(
        facility_cols_df,
        on=["address_id", "spatial_id"] + station_information,
        how="left",
        nulls_equal=True,
    )

    facilities = (
        data.select(
            ["facility_id", "operator_id", "spatial_id"]
            + facility_designators
            + ["coord_points_facility"]
        )
        .unique()
        .with_columns(
            pl.when(pl.col("coord_points_facility"))
            .then(pl.col("spatial_id"))
            .otherwise(None)
        )
        .drop("coord_points_facility")
    ).unique()

    columns = (
        data.select(
            ["column_id", "facility_id", "spatial_id", "address_id"]
            + column_designators
            + ["coord_points_column"]
        )
        .unique()
        .with_columns(
            pl.when(pl.col("coord_points_column"))
            .then(pl.col("spatial_id"))
            .otherwise(None)
        )
        .drop("coord_points_column")
    )

    addresses = (
        data.select(["address_id", "street", "zip_code", "postal_name"])
        .unique()
        .with_columns(pl.lit("FR").alias("country_code"))
        .with_columns(pl.lit("FR").alias("country"))
        .rename({"address_id": "id"})
    )
    coordinates = (
        data.select(["spatial_id", "longitude", "latitude"])
        .with_columns(
            pl.col("longitude").round(5),
            pl.col("latitude").round(5),
        )
        .unique(subset="spatial_id")
        .rename({"spatial_id": "id"})
    )

    geolocations = (
        pl.concat(
            [
                columns.select(["spatial_id", "address_id"]),
                facilities.select(["spatial_id", "address_id"]),
            ]
        )
        .unique()
        .with_columns(
            pl.struct("address_id", "spatial_id")
            .map_elements(
                lambda row: (
                    "A"
                    + str(row["address_id"]).replace("None", "000000000")
                    + "S"
                    + str(row["spatial_id"]).replace("None", "0000000000000")
                ),
                return_dtype=pl.String,
            )
            .alias("geolocation_id")
        )
        .select(["geolocation_id", "spatial_id", "address_id"])
    )

    facilities = (
        (
            facilities.join(
                geolocations,
                on=["spatial_id", "address_id"],
                how="left",
                nulls_equal=True,
            )
            .select(
                ["facility_id", "operator_id", "geolocation_id"] + facility_designators
            )
            .drop("address_id")
        )
        .rename({"facility_id": "id", "nom_station": "name"})
        .unique(
            subset=["id"]
        )  # Basically a nuke, like 40 stations had some information loss :(
    )

    columns = (
        columns.join(
            geolocations, on=["spatial_id", "address_id"], how="left", nulls_equal=True
        )
        .select(["column_id", "facility_id", "geolocation_id"] + column_designators)
        .drop(["id_station_itinerance", "id_station_local"])
    ).rename(
        {
            "column_id": "id",
            "date_mise_en_service": "commissioning_date",
            "nbre_pdc": "charger_amount",
        }
    )

    # Extract EVSE information
    evses_full = data.select(["column_id"] + evse_information)

    evses_full = (
        evses_full.with_columns(
            pl.when(pl.col("column_id") == pl.col("id_pdc_itinerance"))
            .then(pl.col("id_pdc_itinerance") + "E")
            .otherwise(pl.col("id_pdc_itinerance"))
            .fill_null(pl.col("id_pdc_local"))
            .fill_null(pl.col("column_id"))
            .alias("id_pre"),
        )
        .with_columns(
            pl.col("id_pre").cum_count().over("id_pre").alias("_dup_count"),
        )
        .with_columns(
            pl.when(pl.col("id_pre").is_duplicated())
            .then(pl.col("id_pre") + pl.col("_dup_count").cast(str))
            .otherwise(pl.col("id_pre"))
        )
        .drop("_dup_count")
        .rename({"id_pre": "id"})
    )

    evses = evses_full.select(["id", "column_id"])

    connections_full = evses_full.select(
        [
            "id",
            "puissance_nominale",
            "prise_type_ef",
            "prise_type_2",
            "prise_type_combo_ccs",
            "prise_type_chademo",
            "prise_type_autre",
        ]
    )

    connections_stacked = (
        connections_full.with_columns(
            pl.col("prise_type_ef")
            .str.to_lowercase()
            .replace_strict({"true": True, "false": False, "0": False, "1": True}),
            pl.col("prise_type_2")
            .str.to_lowercase()
            .replace_strict({"true": True, "false": False, "0": False, "1": True}),
            pl.col("prise_type_combo_ccs")
            .str.to_lowercase()
            .replace_strict({"true": True, "false": False, "0": False, "1": True}),
            pl.col("prise_type_chademo")
            .str.to_lowercase()
            .replace_strict({"true": True, "false": False, "0": False, "1": True}),
            pl.col("prise_type_autre")
            .str.to_lowercase()
            .replace_strict({"true": True, "false": False, "0": False, "1": True}),
        )
        .with_columns(
            pl.when(pl.col("prise_type_ef"))
            .then(pl.lit("DOMESTICF"))
            .otherwise(None)
            .alias("DOMESTICF"),
            pl.when(pl.col("prise_type_2"))
            .then(pl.lit("IEC62196T2"))
            .otherwise(None)
            .alias("IEC62196T2"),
            pl.when(pl.col("prise_type_combo_ccs"))
            .then(pl.lit("IEC62196T2COMBO"))
            .otherwise(None)
            .alias("IEC62196T2COMBO"),
            pl.when(pl.col("prise_type_chademo"))
            .then(pl.lit("CHADEMO"))
            .otherwise(None)
            .alias("CHADEMO"),
            pl.when(pl.col("prise_type_autre"))
            .then(pl.lit("CONNECTOR"))
            .otherwise(None)
            .alias("CONNECTOR"),
        )
        .unpivot(
            on=[
                "DOMESTICF",
                "IEC62196T2",
                "IEC62196T2COMBO",
                "CHADEMO",
                "CONNECTOR",
            ],
            index=["id", "puissance_nominale"],
            variable_name="standard",
        )
        .drop("value")
        .rename({"puissance_nominale": "max_power"})
    ).with_columns(pl.col("max_power") * 1000)

    connectors = (
        connections_stacked.select("standard", "max_power")
        .unique()
        .with_row_index()
        .with_columns(
            pl.col("index").map_elements(
                lambda x: f"IRVE_CONN_{str(x).zfill(8)}", return_dtype=str
            )
        )
        .rename({"index": "id"})
    )

    connections = (
        connections_stacked.join(connectors, on=["max_power", "standard"])
        .rename({"id_right": "connector_id", "id": "evse_id"})
        .drop(["max_power", "standard"])
    )

    data = {
        "addresses": addresses,
        "facilities": facilities,
        "columns": columns,
        "geolocations": geolocations.rename({"geolocation_id": "id"}),
        "operators": agents.rename({"operator": "name"}).with_columns(
            pl.lit("operator").alias("type")
        ),
        "connectors": connectors,
        "connections": connections,
        "evse": evses,
        "spatial": coordinates,
    }

    return data


def process_resources(data_dict, annotations, filenames, foreign_key_map):
    """
    Process all resources by describing, annotating, and creating resource dictionaries.
    """
    resources = []
    for key, data in data_dict.items():
        resource_name = filenames[key]
        primary_key = "id"
        if key == "connections":
            primary_key = None
        foreign_keys = foreign_key_map.get(key, None)
        resource = describe_and_annotate(
            data, annotations, resource_name, primary_key, foreign_keys
        )
        resources.append(resource)
    return resources


def create_foreign_key(fields, reference_resource, reference_fields):
    """
    Create a foreign key dictionary.
    """
    return {
        "fields": fields,
        "reference": {"resource": reference_resource, "fields": reference_fields},
    }


def write_annotated_irve_csv(
    data: Dict[str, Any], directory: str, identifier: str, annotations_file: str
):
    # Define foreign key mappings
    with open(annotations_file, "r", encoding="utf-8") as f:
        annotations = yaml.safe_load(f)
    filenames = {k: f"{k}" for k in data.keys()}
    foreign_key_map = {
        "columns": [
            create_foreign_key(["facility_id"], filenames["facilities"], ["id"]),
            create_foreign_key(["geolocation_id"], filenames["geolocations"], ["id"]),
        ],
        "connections": [
            create_foreign_key(["evse_id"], filenames["evse"], ["id"]),
            create_foreign_key(["connector_id"], filenames["connectors"], ["id"]),
        ],
        "evse": [
            create_foreign_key(["column_id"], filenames["columns"], ["id"]),
        ],
        "facilities": [
            create_foreign_key(["operator_id"], filenames["operators"], ["id"]),
            create_foreign_key(["geolocation_id"], filenames["geolocations"], ["id"]),
        ],
        "geolocations": [
            create_foreign_key(["spatial_id"], filenames["spatial"], ["id"]),
            create_foreign_key(["address_id"], filenames["addresses"], ["id"]),
        ],
    }

    resources = process_resources(data, annotations, filenames, foreign_key_map)

    # Update annotations
    annotations_new = deepcopy(annotations)
    annotations_new["resources"] = resources

    (p := Path(f"{directory}/{identifier}")).mkdir(exist_ok=True)
    with open(
        f"{p}/datapackage.json",
        "w",
        encoding="utf8",
    ) as output:
        json.dump(annotations_new, output, indent=4, ensure_ascii=False)

    write_irve_csv(data, directory, identifier)


def describe_and_annotate(
    data, annotations, resource_name, primary_key, foreign_keys=None
):
    """
    Describe the schema of the data, annotate it, and return the resource dictionary.
    """
    schema = fl.Schema.describe(data)
    schema_dict = schema.to_dict()

    fields = OrderedDict({f["name"]: f for f in schema_dict["fields"]})
    if "resources" in annotations:
        annotation_fields = {
            f["name"]: f
            for f in annotations["resources"][0]["schema"]["fields"]
            if f["name"] in fields.keys()
        }

        # Add common annotations
        annotation_fields["id"] = {"description": "Unique identifier"}
        for k, v in annotation_fields.items():
            fields[k].update(v)

    # Remove constraints from "id" if present
    if "id" in fields and "constraints" in fields["id"]:
        fields["id"].pop("constraints")

    fields_list = [v for v in fields.values()]
    resource = {
        "profile": "tabular-data-resource",
        "name": resource_name,
        "path": f"{resource_name}.csv",
        "format": "csv",
        "encoding": "utf-8",
        "schema": {
            "fields": fields_list,
        },
    }
    if primary_key is not None:
        resource["schema"]["primaryKey"] = primary_key

    if foreign_keys:
        resource["schema"]["foreignKeys"] = foreign_keys

    return resource


def write_irve_csv(data, output_path, identifier):
    (output_path := Path(output_path)).mkdir(exist_ok=True, parents=True)
    (out_path := output_path.joinpath(identifier)).mkdir(exist_ok=True, parents=True)

    data["addresses"].write_csv(f"{out_path}/addresses.csv")
    data["facilities"].write_csv(f"{out_path}/facilities.csv")
    data["columns"].write_csv(f"{out_path}/columns.csv")
    data["geolocations"].write_csv(f"{out_path}/geolocations.csv")
    data["operators"].write_csv(f"{out_path}/operators.csv")
    data["connectors"].write_csv(f"{out_path}/connectors.csv")
    data["connections"].write_csv(f"{out_path}/connections.csv")
    data["evse"].write_csv(f"{out_path}/evse.csv")
    data["spatial"].write_csv(out_path.joinpath("spatial.csv"))
