from collections import OrderedDict
from pathlib import Path
from copy import deepcopy
from typing import Any
from typing import Dict
import frictionless as fl


def annotate_datex2(data, metadata={}, annotations={}):
    descriptor = {}
    descriptor["name"] = metadata.get("id", "").lower()
    descriptor["title"] = metadata.get("name", None)
    descriptor["id"] = metadata.get("id", "")
    descriptor["description"] = (
        "Tabular extract of DATEX II charging infrastructure data"
    )
    descriptor["language"] = ["en-GB"]
    descriptor["subject"] = [
        {
            "name": "vehicle charging station",
            "path": "http://openenergy-platform.org/ontology/oeo/OEO_00320040",
        }
    ]
    descriptor["keywords"] = ["electric vehicles", "charging station", "mobility"]
    country_code = metadata.get("id", "NA-").split("-")[0]
    descriptor["spatial"] = {
        "location": country_code,
        "extent": country_code,
        "resolution": "point",
    }
    descriptor["sources"] = [
        {
            "title": metadata.get("name", None),
            "description": metadata.get("name", None),
            "path": metadata.get("metadata_url", None),
            "licenses": [match_license(metadata)],
        },
    ]

    descriptor["licenses"] = [
        {
            "name": "CC BY 4.0",
            "title": "Attribution 4.0 International",
            "path": "https://creativecommons.org/licenses/by/4.0",
            "attribution": "Copyright (c) 2025 German Aerospace Center (DLR)",
            "instruction": "You are free to copy and redistribute the material in any medium or format. You are free to remix, transform, and build upon the material for any purpose, even commercially.",
        }
    ]

    filenames = {k: f"{k}" for k in data.keys()}

    geo_fks = [create_foreign_key(["spatial_id"], filenames["spatial"], ["id"])]
    if "addresses" in filenames:
        geo_fks.append(
            create_foreign_key(["address_id"], filenames["addresses"], ["id"])
        )

    facility_fks = [
        create_foreign_key(["geolocation_id"], filenames["geolocations"], ["id"]),
    ]
    if "operators" in filenames:
        facility_fks.append(
            create_foreign_key(["operator_id"], filenames["operators"], ["id"]),
        )

    foreign_key_map = {
        "facilities": facility_fks,
        "geolocations": geo_fks,
    }
    if "evse" in filenames:
        foreign_key_map["evse"] = [
            create_foreign_key(["facility_id"], filenames["facilities"], ["id"]),
            create_foreign_key(["geolocation_id"], filenames["geolocations"], ["id"]),
        ]
    if "connections" in filenames:
        foreign_key_map["connections"] = [
            create_foreign_key(["evse_id"], filenames["evse"], ["id"]),
            create_foreign_key(["connector_id"], filenames["connectors"], ["id"]),
        ]

    resources = process_resources(data, annotations, filenames, foreign_key_map)

    descriptor["resources"] = resources

    return descriptor


def match_license(row: Dict[str, Any]):
    lic_text: None | str = row.get("license", None)
    lic = {}
    attribution = row.get("provider", None)
    if lic_text is None:
        lic["name"] = "unkwown"
    elif lic_text.upper() == "CC-BY-4.0":
        lic["name"] = "CC-BY-4.0"
        lic["path"] = "https://creativecommons.org/licenses/by/4.0"
        lic["attribution"] = (
            attribution if attribution is not None else row.get("source", "")
        )
        lic["instruction"] = (
            "You are free to copy and redistribute the material in any medium or format. You are free to remix, transform, and build upon the material for any purpose, even commercially."
        )
    elif lic_text.upper() == "CC0-1.0":
        lic["name"] = "CC0-1.0"
        lic["path"] = "https://creativecommons.org/publicdomain/zero/1.0/"
        lic["instruction"] = (
            "You can copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission."
        )
    return lic


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


def describe_and_annotate(
    data, annotations, resource_name, primary_key, foreign_keys=None
):
    """
    Describe the schema of the data, annotate it, and return the resource dictionary.
    """
    schema = fl.Schema.describe(data)
    schema_dict = schema.to_dict()
    annotation_schema = [
        s for s in annotations["resources"] if s["name"] == resource_name
    ]
    fields = OrderedDict({f["name"]: f for f in schema_dict["fields"]})
    if "resources" in annotations:
        annotation_fields = {
            f["name"]: f
            for f in annotation_schema[0]["schema"]["fields"]
            if f["name"] in fields.keys()
        }

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
        resource["schema"]["primaryKey"] = [primary_key]

    if foreign_keys:
        resource["schema"]["foreignKeys"] = foreign_keys

    return resource
