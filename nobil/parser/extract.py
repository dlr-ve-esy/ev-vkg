import json
from pathlib import Path
from typing import Dict, List
import polars as pl
from zlib import crc32
import re


def nobil_extract_data(filepath: str):
    with open(filepath, "r") as f:
        doc = json.load(f)

    facilities: List[Dict] = []
    operators: List[Dict] = []
    geolocations: List[Dict] = []
    evses_pre: List[Dict] = []

    operator_memory: Dict = {}
    addresses: Dict = {}
    coordinates: Dict = {}

    country_map = {
        "NOR": "NO",
        "ISL": "IS",
        "DAN": "DK",
        "FIN": "FI",
        "SWE": "SE",
    }

    for cs in doc["chargerstations"]:
        csmd = cs["csmd"]
        attr = cs["attr"]
        # Extract facility data
        facility = {}
        facility["id"] = csmd["id"]
        facility["source_id"] = "NO-20250120-NOBIL-NOB"
        facility["name"] = csmd["name"]

        # Extract operator data
        operator_hash = int(crc32("".join((csmd["Operator"])).encode("utf8")))
        if operator_hash not in operator_memory:
            operator_memory[operator_hash] = csmd["Operator"]
            operators.append(
                {"id": operator_hash, "name": csmd["Operator"], "type": "operator"}
            )
        facility["last_updated"] = csmd["Updated"]
        facility["operator_id"] = operator_hash

        # Extract addresses data
        geolocation = {}
        address = {}
        address["street"] = csmd["Street"]
        address["locator_designator"] = csmd["House_number"]
        address["postal_name"] = csmd["City"]
        address["zip_code"] = csmd["Zipcode"]
        address["state"] = csmd["County"]
        address["country"] = country_map.get(csmd["Land_code"], "NO")
        address["last_updated"] = csmd["Updated"]

        ad_hash = int(crc32("".join((address.values())).encode("utf8")))
        if ad_hash not in addresses:
            ad_temp = {}
            ad_temp["id"] = ad_hash
            ad_temp.update(address)
            addresses[ad_hash] = ad_temp

        geolocation["address_id"] = ad_hash

        coord_maybe = tuple(
            map(float, csmd["Position"].replace("(", "").replace(")", "").split(","))
        )
        coordinate_hash = int(
            str(int(coord_maybe[0] * 100000))
            + str(int(coord_maybe[1] * 100000)).replace("-", "1")
        )
        if coordinate_hash not in coordinates:
            coordinates[coordinate_hash] = coord_maybe
        geolocation["spatial_id"] = coordinate_hash

        geolocation["id"] = (
            "A" + str(ad_hash) + "S" + str(coordinate_hash).zfill(6)[0:6]
        )
        geolocations.append(geolocation)
        facility["geolocation_id"] = geolocation["id"]
        facilities.append(facility)
        if csmd["id"] == 7791:
            pass
        for i, conn in attr["conn"].items():
            evse = {}
            evse["evseid"] = conn.get("28", {}).get("attrval", None)
            evse_id = conn.get("27", None)
            if evse_id is None:
                evse["id"] = csmd["International_id"] + f"_{i}"
            elif evse_id == "":
                evse["id"] = evse["evseid"]
            else:
                if "," in evse_id["attrval"]:
                    pre = ""
                else:
                    if evse_id["attrval"].isnumeric():
                        pre = csmd["Land_code"] + "_"
                    else:
                        pre = ""
                evse["id"] = pre + evse_id["attrval"]
            evse["facility_id"] = csmd["id"]
            evse["connector_id"] = conn.get("29", {}).get("attrval", None)
            evse["last_updated"] = csmd["Updated"]
            evse["source_id"] = "NO-20250120-NOBIL-NOB"
            evse["power_pre"] = conn.get("5", {}).get("trans", None)
            evse["standard_pre"] = conn.get("4", {}).get("trans", None)
            evse["coupling"] = (
                "cable"
                if conn.get("25", {}).get("trans", "No").lower() == "yes"
                else "socket"
            )
            evse["pre_voltage"] = conn.get("12", {}).get("attrval", None)
            evse["pre_amperage"] = conn.get("31", {}).get("attrval", None)
            evses_pre.append(evse)

    ev_df = pl.DataFrame(evses_pre)
    # Some of the ids are annotated as list, seems to be that someone used this field in an unintended way.
    # # regex for evse ids
    evse_id_regex_strict = (
        r"^[A-Z]{2}[\*\-]*[A-Z0-9]{3}[\*\-]*[PE][A-Z0-9]{1,20}([\*\-]*[A-Z0-9])*$"
    )
    evse_id_regex_weak = (
        r"[A-Z]{2}[\*\-]*[A-Z0-9]{3}[\*\-]*[PE][A-Z0-9]{1,20}([\*\-]*[A-Z0-9])*"
    )
    # ^[A-Z]{2}[\*\-]*[A-Z0-9]{3}[\*\-]*[PE][A-Z0-9]{1,20}([\*\-]*[A-Z0-9])*$
    ev_df = ev_df.with_columns(
        pl.when(pl.col("connector_id").str.contains(evse_id_regex_strict))
        .then(pl.col("connector_id"))
        .when(pl.col("evseid").str.contains(evse_id_regex_strict))
        .then(pl.col("evseid"))
        .when(pl.col("id").str.contains(evse_id_regex_strict))
        .then(pl.col("id"))
        .when(pl.col("id").str.contains(evse_id_regex_weak))
        .then(pl.col("id"))
        .when(pl.col("evseid").str.contains(evse_id_regex_weak))
        .then(pl.col("evseid"))
        .otherwise(pl.col("id"))
        .alias("proper_id")
    )

    FILTER = (
        (pl.col("proper_id").str.contains(evse_id_regex_weak))
        & (~pl.col("proper_id").str.contains(evse_id_regex_strict))
    ) | (pl.col("proper_id").str.contains(","))

    ev_ugly = ev_df.filter(FILTER)

    ev_decent = ev_df.filter(~FILTER)

    cleaned_df = pl.DataFrame(schema=ev_df.schema)

    u_partition = ev_ugly.partition_by("proper_id", as_dict=True)

    for ids, df in u_partition.items():
        size = df.shape[0]
        if (
            (
                capture := re.search(
                    r"([A-Z]{2}[\*\-]*[A-Z0-9]{3}[\*\-]*[PE])([A-Z0-9]{1,20})\s+-\s+[A-Z]{2}[\*\-]*[A-Z0-9]{3}[\*\-]*[PE]([A-Z0-9]{1,20})",
                    ids[0],
                )
            )
            is not None
        ) or (
            (
                capture := re.search(
                    r"([A-Z]{2}[\*\-]*[A-Z0-9]{3}[\*\-]*[PE][A-Z0-9]{1,20}[\*\-])([A-Z0-9]+)\s+\-\s+[A-Z]{2}[\*\-]*[A-Z0-9]{3}[\*\-]*[PE][A-Z0-9]{1,20}[\*\-]([A-Z0-9]+)",
                    ids[0],
                )
            )
            is not None
        ):
            prefix = capture.group(1)
            start = capture.group(2)
            end = capture.group(3)
            dist_ids = list([f"{prefix}{r}" for r in range(int(start), int(end) + 1)])
            if len(dist_ids) == size:
                df = df.with_columns(pl.Series(name="proper_id", values=dist_ids))
            elif len(dist_ids) > size:
                df = df.with_columns(
                    pl.Series(name="proper_id", values=dist_ids[:size])
                )
            elif size == len((naive := re.split(r"\s-\s*", ids[0]))):
                df = df.with_columns(pl.Series(name="proper_id", values=naive))
            else:
                diff = size - (int(end) - int(start)) + 1
                dist_ids = list(
                    [f"{prefix}{r}" for r in range(int(start), int(end) + diff)]
                )
                df = df.with_columns(pl.Series(name="proper_id", values=dist_ids))
        # Messy case because someone was very smart and decided to define their IDs as an equation
        elif (
            capture := re.search(
                r"(SE-MER-E2344)(\d\d\d) -&gt; SE-MER-E2344(\d\d\d) &amp; SE-MER-E2344(\d\d\d) -&gt; SE-MER-E2344(\d\d\d)",
                ids[0],
            )
        ) is not None:
            prefix = capture.group(1)
            start_1 = capture.group(2)
            end_1 = capture.group(3)
            start_2 = capture.group(4)
            end_2 = capture.group(5)
            dist_ids_1 = list(
                [f"{prefix}{r}" for r in range(int(start_1), int(end_1) + 1)]
            )
            dist_ids_2 = list(
                [f"{prefix}{r}" for r in range(int(start_2), int(end_2) + 1)]
            )
            dist_ids = dist_ids_1 + dist_ids_2
            df = df.with_columns(pl.Series(name="proper_id", values=dist_ids))
        elif "," in ids[0]:
            single_ids = list(map(lambda x: x.strip(), ids[0].split(",")))
            if len(single_ids) == size:
                df = df.with_columns(pl.Series(name="proper_id", values=single_ids))
            else:
                facility_id = df["facility_id"][0]
                artificial_ids = [
                    f"{facility_id}{str(f).zfill(4)}" for f in range(0, df.shape[0])
                ]
                df = df.with_columns(pl.Series(name="proper_id", values=artificial_ids))
        cleaned_df = pl.concat([cleaned_df, df])

    ev_unified = pl.concat([ev_decent, cleaned_df])
    ev_unified = (
        ev_unified.drop("id")
        .drop("connector_id")
        .drop("evseid")
        .rename({"proper_id": "id"})
    ).with_columns(
        pl.col("id")
        .str.replace(r"\s-\s(\d+)", "")
        .str.replace(r"-\s", "-")
        .str.replace_all(r"\s", "-")
    )
    connector_types: Dict[str | None, List[str]] = {
        "Type1/Type2": ["iec62196T1", "iec62196T2"],
        "CHAdeMO": ["chademo"],
        "Type 2 + Schuko": ["iec62196T2", "domesticF"],
        None: ["connector"],
        "Unspecified\n": ["connector"],
        "Tesla Connector Model": ["tesla"],
        "Type 1": ["iec62196T1"],
        "Type 2": ["iec62196T2"],
        "CCS/Combo": ["iec62196T2COMBO"],
    }
    ev_unified = ev_unified.filter(pl.col("standard_pre").is_in(connector_types))
    ev_unified = ev_unified.with_columns(
        pl.col("standard_pre")
        .map_elements(
            lambda x: connector_types.get(x, ["connector"]), return_dtype=List[str]
        )
        .alias("standard")
    ).explode("standard")
    ev_unified = ev_unified.with_columns(
        pl.col("power_pre")
        .str.extract_groups(r"(\d+[,\.]*\d+)\s*[Kk]W")
        .struct[0]
        .str.replace_all(",", ".")
        .cast(float)
        .mul(1000)
        .cast(int)  # convert to Watts for consistency across graphs
        .alias("max_power")
    )

    ev_unified = (
        ev_unified.with_columns(
            pl.col("pre_voltage")
            .str.replace("200 - 1 000", "1000")
            .str.replace("200-920", "920")
            .str.replace("150-920", "920")
            .str.extract_groups(r"(\d+)")
            .struct[0]
            .alias("pre_voltage_b")
        )
        .with_columns(
            pl.when(pl.col("pre_voltage_b").is_null())
            .then(pl.col("power_pre").str.extract_groups(r"(\d+)V").struct[0])
            .when(pl.col("pre_voltage_b") == "0")
            .then(pl.col("power_pre").str.extract_groups(r"(\d+)V").struct[0])
            .otherwise(pl.col("pre_voltage_b"))
            .alias("max_voltage")
        )
        .with_columns(
            pl.col("pre_amperage")
            .str.replace("A", "")
            .str.replace("500 - 250", "500")
            .str.extract_groups(r"(\d+)")
            .struct[0]
            .alias("pre_amperage_b")
        )
        .with_columns(
            pl.when(pl.col("pre_amperage_b").is_null())
            .then(pl.col("power_pre").str.extract_groups(r"(\d+)A").struct[0])
            .when(pl.col("pre_amperage_b") == "0")
            .then(pl.col("power_pre").str.extract_groups(r"(\d+)A").struct[0])
            .otherwise(pl.col("pre_amperage_b"))
            .alias("max_amperage")
        )
    )

    evse_connections = ev_unified.select(
        pl.col("id").alias("evse_id"),
        pl.col("facility_id"),
        pl.col("last_updated"),
        pl.col("source_id"),
        pl.col("coupling"),
        pl.col("standard"),
        pl.col("max_power"),
        pl.col("max_voltage"),
        pl.col("max_amperage"),
        pl.concat_str(
            pl.col("coupling").fill_null(""),
            pl.col("standard").fill_null(""),
            pl.col("max_power").cast(str).fill_null(""),
            pl.col("max_voltage").cast(str).fill_null(""),
            pl.col("max_amperage").cast(str).fill_null(""),
        )
        # .map_elements(lambda x: int(crc32(x.encode("utf8"))))
        .alias("hash"),
    )

    connectors_pre = (
        evse_connections.select(
            pl.col("hash"),
            pl.col("coupling"),
            pl.col("standard"),
            pl.col("max_power"),
            pl.col("max_voltage"),
            pl.col("max_amperage"),
        )
        .unique()
        .with_columns(
            pl.col("hash")
            .map_elements(lambda x: int(crc32(x.encode("utf8"))), return_dtype=int)
            .alias("id")
        )
    )

    connector_id = connectors_pre.select(pl.col("hash"), pl.col("id"))

    connections = evse_connections.join(
        connector_id, left_on="hash", right_on="hash"
    ).select(pl.col("evse_id"), pl.col("id").alias("connector_id"))

    evse_out = ev_unified.select(
        pl.col("id"),
        pl.col("source_id"),
        pl.col("facility_id"),
        pl.lit(None).alias("geolocation_id"),
        pl.col("id").alias("evseid"),
        pl.col("last_updated"),
    ).unique()

    connectors = connectors_pre.select(
        pl.col("id"),
        pl.col("coupling"),
        pl.col("standard"),
        pl.col("max_voltage"),
        pl.col("max_amperage"),
        pl.col("max_power"),
    )

    data = {
        "addresses": pl.DataFrame(list(addresses.values())),
        "facilities": pl.DataFrame(facilities),
        "geolocations": pl.DataFrame(geolocations).unique(subset="id"),
        "operators": pl.DataFrame(operators),
        "connectors": pl.DataFrame(connectors),
        "connections": pl.DataFrame(connections),
        "evse": pl.DataFrame(evse_out),
        "spatial": pl.DataFrame(
            [
                {"id": i, "latitude": cmp[0], "longitude": cmp[1]}
                for (i, cmp) in coordinates.items()
            ],
            infer_schema_length=None,
        ),
    }

    return data


def write_nobil_csv(data, output_path, identifier):
    (output_path := Path(output_path)).mkdir(exist_ok=True, parents=True)
    (out_path := output_path.joinpath(identifier)).mkdir(exist_ok=True, parents=True)

    data["addresses"].write_csv(f"{out_path}/addresses.csv")
    data["facilities"].write_csv(f"{out_path}/facilities.csv")
    data["geolocations"].write_csv(f"{out_path}/geolocations.csv")
    data["operators"].write_csv(f"{out_path}/operators.csv")
    data["connectors"].write_csv(f"{out_path}/connectors.csv")
    data["connections"].write_csv(f"{out_path}/connections.csv")
    data["evse"].write_csv(f"{out_path}/evse.csv")
    data["spatial"].write_csv(out_path.joinpath("spatial.csv"))


if __name__ == "__main__":
    nobil_data = nobil_extract_data("NOBIL.json")
    write_nobil_csv(nobil_data, "data", "NOBIL")
