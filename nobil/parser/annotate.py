# SPDX-FileCopyrightText: Copyright (c) 2023 German Aerospace Center (DLR)
# SPDX-License-Identifier: BSD-3-Clause
from pathlib import Path
from copy import deepcopy
from typing import Any
from typing import Dict
import frictionless as fl
import yaml
from collections import OrderedDict
import json
from .extract import write_nobil_csv, nobil_extract_data


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


def write_annotated_nobil_csv(
    data: Dict[str, Any], directory: str, identifier: str, annotations_file: str
):
    # Define foreign key mappings
    with open(annotations_file, "r", encoding="utf-8") as f:
        annotations = yaml.safe_load(f)
    filenames = {k: f"{k}" for k in data.keys()}
    foreign_key_map = {
        "connections": [
            create_foreign_key(["evse_id"], filenames["evse"], ["id"]),
            create_foreign_key(["connector_id"], filenames["connectors"], ["id"]),
        ],
        "evse": [
            create_foreign_key(["facility_id"], filenames["facilities"], ["id"]),
            create_foreign_key(["geolocation_id"], filenames["geolocations"], ["id"]),
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

    write_nobil_csv(data, directory, identifier)


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
