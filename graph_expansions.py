from pathlib import Path
from typing import Optional
import polars as pl
from maplib import Mapping
import re
import datetime

CHIO = "https://dlr-ve-esy.github.io/charging-ontology/"
VKG = "https://gitlab.dlr.de/vkg#"

CHALLENGE_MODE = True
# USE THE polars sample API to do the challenge mode


def map_plug_standards(text: str) -> str:
    match text.lower():
        # Domestic patterns
        case "domestica" | "domestic_a":
            out = f"{CHIO}CHIO_00000071"
        case "domesticb" | "domestic_b":
            out = f"{CHIO}CHIO_00000072"
        case "domesticc" | "domestic_c":
            out = f"{CHIO}CHIO_00000073"
        case "domesticd" | "domestic_d":
            out = f"{CHIO}CHIO_00000074"
        case "domestice" | "domestic_e":
            out = f"{CHIO}CHIO_00000075"
        case "domesticf" | "domestic_f" | "schuko":
            out = f"{CHIO}CHIO_00000076"
        case "domesticg" | "domestic_g":
            out = f"{CHIO}CHIO_00000077"
        case "domestich" | "domestic_h":
            out = f"{CHIO}CHIO_00000078"
        case "domestici" | "domestic_i":
            out = f"{CHIO}CHIO_00000079"
        case "domesticj" | "domestic_j":
            out = f"{CHIO}CHIO_00000080"
        case "domestick" | "domestic_k":
            out = f"{CHIO}CHIO_00000081"
        case "domesticl" | "domestic_l":
            out = f"{CHIO}CHIO_00000082"
        # Industrial Patterns
        case "iec_60309_2_single_16" | "iec60309x2single16" | "iec60309_2single16":
            out = f"{CHIO}CHIO_00000062"
        case "iec_60309_2_three_16" | "iec60309x2three16" | "iec60309_2three16":
            out = f"{CHIO}CHIO_00000063"
        case "iec_60309_2_three_32" | "iec60309x2three32" | "iec60309_2three32":
            out = f"{CHIO}CHIO_00000064"
        case "iec_60309_2_three_64" | "iec60309x2three64" | "iec60309_2three64":
            out = f"{CHIO}CHIO_00000065"
        # AC Patterns
        case "iec62196t1" | "type1" | "type_1" | "iec_62196_t1":
            out = f"{CHIO}CHIO_00000025"
        case "iec62196t2" | "type2" | "type_2" | "iec_62196_t2" | "cee5" | "mennekes":
            out = f"{CHIO}CHIO_00000026"
        # DC Patterns
        case "iec62196t1combo" | "iec_62196_t1_combo":
            out = f"{CHIO}CHIO_00000027"
        case "iec62196t2combo" | "iec_62196_t2_combo":
            out = f"{CHIO}CHIO_00000028"
        case "chademo":
            out = f"{CHIO}CHIO_00000024"
        case "tesla" | "tesla_s" | "teslas" | "nacs":
            out = f"{CHIO}CHIO_00000043"
        case "teslar" | "tesla_r" | "roadster" | "tesla_roadster":
            out = f"{CHIO}CHIO_00000045"
        case _:
            # print(f"Unkown pattern: {text}")
            out = f"{CHIO}CHIO_00000015"  # TODO: Add logging
    return out


def map_coupling_method(text: str) -> str:
    match text.lower():
        case "cable":
            out = f"{CHIO}CHIO_00000013"
        case "socket":
            out = f"{CHIO}CHIO_00000014"
        case _:
            # print(f"Unkown pattern: {text}. Defaulting to cable")
            out = f"{CHIO}CHIO_00000013"
    return out


def expand_relational_csv(
    name: str,
    path: str,
    mapping: Optional[Mapping] = None,
    challenge: bool = False,
    country: Optional[str] = None,
):
    if mapping is None:
        with open("templates/evse.stottr", "r") as d:
            vkg_evse = d.read()
        with open("templates/common.stottr", "r") as d:
            vkg_common = d.read()
        m = Mapping([vkg_common, vkg_evse])
    else:
        m = mapping
    pl.Config.set_fmt_str_lengths(150)

    if (p := Path(f"{path}/facilities.csv")).exists():
        facility: pl.DataFrame = pl.read_csv(p)
        if challenge:
            facility = facility.sample(5)
        geo_ids = facility["geolocation_id"].unique()
        operator_ids = facility["operator_id"].unique()
        facility_ids = facility["id"].unique()
        facility = facility.select(
            (VKG + pl.col("id").cast(str)).alias("facility"),
            (VKG + pl.col("operator_id").cast(str)).alias("operator"),
            (VKG + pl.col("geolocation_id").cast(str)).alias("geolocation"),
            pl.col("id").cast(str).alias("ID"),
        )
        m.expand("vkg-evse:Facility", facility, graph=f"{VKG}{name}")
    if (p := Path(f"{path}/geolocations.csv")).exists():
        geolocations: pl.DataFrame = pl.read_csv(p)
        if challenge:
            geolocations = geolocations.filter(pl.col("id").is_in(geo_ids))
        if (p := Path(f"{path}/spatial.csv")).exists():
            geolocations = geolocations.join(
                pl.read_csv(p), left_on="spatial_id", right_on="id"
            )
        if (p := Path(f"{path}/addresses.csv")).exists():
            geolocations = geolocations.join(
                pl.read_csv(p), left_on="address_id", right_on="id"
            )
        geolocations = geolocations.select(
            (VKG + pl.col("id").cast(str)).alias("geolocation"),
            pl.format("POINT ({} {})", pl.col("longitude"), pl.col("latitude"))
            .cast(str)
            .alias("centroid"),
            geolocations.get_column("street", default=pl.lit(None)).alias("address"),
            geolocations.get_column("postal_name", default=pl.lit(None)).alias(
                "postal_name"
            ),
            geolocations.get_column("state", default=pl.lit(None)).alias("state"),
            geolocations.get_column("zip_code", default=pl.lit(None))
            .cast(str)
            .alias("postal_code"),
            geolocations.get_column("country", default=pl.lit(country))
            .fill_null(country)
            .alias("country"),
        )
        m.expand("vkg-evse:GeoLocation", geolocations, graph=f"{VKG}{name}")

    if (p := Path(f"{path}/operators.csv")).exists():
        operator: pl.DataFrame = pl.read_csv(p)
        if challenge:
            operator = operator.filter(pl.col("id").is_in(operator_ids))
        operator = operator.select(
            (VKG + pl.col("id").cast(str)).alias("operator"),
            pl.col("name").cast(str).alias("label"),
            pl.col("id").cast(str).alias("ID"),
            pl.col("type")
            .map_elements(
                lambda x: "https://www.commoncoreontologies.org/ont00001006"
                if x == "operator"
                else pl.Null,
                return_dtype=pl.String,
            )
            .alias("role"),
        )
        m.expand("vkg-evse:Operator", operator, graph=f"{VKG}{name}")
    if (p := Path(f"{path}/evses.csv")).exists():
        evse: pl.DataFrame = pl.read_csv(p)
        if challenge:
            evse = evse.filter(pl.col("facility_id").is_in(facility_ids))
        evse_ids = evse["id"].unique()
        evse = evse.select(
            (VKG + pl.col("id").cast(str)).alias("evse"),
            (VKG + pl.col("facility_id").cast(str)).alias("facility"),
            pl.col("id").cast(str).alias("ID"),
            pl.col("evseid").cast(str).alias("altID"),
        )
        m.expand("vkg-evse:EVSEColumn", evse, graph=f"{VKG}{name}")

    if (p := Path(f"{path}/connections.csv")).exists():
        connections: pl.DataFrame = pl.read_csv(p)
        if challenge:
            connections = connections.filter(pl.col("evse_id").is_in(evse_ids))
        if (p := Path(f"{path}/connectors.csv")).exists():
            connections = connections.join(
                pl.read_csv(p), left_on="connector_id", right_on="id"
            ).select(
                (VKG + pl.col("evse_id").cast(str)).alias("evse"),
                pl.col("standard")
                .map_elements(map_plug_standards, return_dtype=pl.String)
                .alias("pattern"),
                pl.col("coupling").map_elements(
                    map_coupling_method, return_dtype=pl.String
                ),
                pl.col("max_voltage").cast(float),
                pl.col("max_amperage").cast(float),
                pl.col("max_power").cast(float),
            )
            m.expand("vkg-evse:Connection", connections, graph=f"{VKG}{name}")


def expand_bnezta(
    name: str,
    path: str,
    mapping: Optional[Mapping] = None,
    challenge: bool = False,
    country: Optional[str] = None,
):
    if mapping is None:
        with open("templates/evse.stottr", "r") as d:
            vkg_evse = d.read()
        with open("templates/common.stottr", "r") as d:
            vkg_common = d.read()
        m = Mapping([vkg_common, vkg_evse])
    else:
        m = mapping
    pl.Config.set_fmt_str_lengths(150)
    pattern = r"(\d{4})(\d{2})(\d{2})"
    matches = re.search(pattern, path)
    if matches:
        yyyy, mm, dd = matches.groups()
    else:
        now = datetime.datetime.now()
        yyyy = str(now.year)
        mm = str(now.month)
        dd = str(now.day)

    if (p := Path(f"{path}/bnetza_facilities_{dd}_{mm}_{yyyy}.csv")).exists():
        facility: pl.DataFrame = pl.read_csv(p)
        if challenge:
            facility = facility.sample(5)
        geo_ids = facility["geolocation_id"].unique()
        operator_ids = facility["operator_id"].unique()
        facility_ids = facility["id"].unique()
        facility = facility.select(
            (VKG + "bnetza_facility" + pl.col("facility_id").cast(str).str.zfill(8)).alias("facility"),
            (VKG + pl.col("operator_id").cast(str)).alias("operator"),
            (VKG + pl.col("geolocation_id").cast(str)).alias("geolocation"),
            pl.col("id").cast(str).alias("ID"),
        )
        m.expand("vkg-evse:Facility", facility, graph=f"{VKG}{name}")

    if (p := Path(f"{path}/bnetza_geolocations_{dd}_{mm}_{yyyy}.csv")).exists():
        geolocations: pl.DataFrame = pl.read_csv(p)
        if challenge:
            geolocations = geolocations.filter(pl.col("id").is_in(geo_ids))
        if (p := Path(f"{path}/bnetza_coordinates_{dd}_{mm}_{yyyy}.csv")).exists():
            geolocations = geolocations.join(
                pl.read_csv(p), left_on="coordinate_id", right_on="id"
            )
        if (p := Path(f"{path}/addresses.csv")).exists():
            geolocations = geolocations.join(
                pl.read_csv(p), left_on="address_id", right_on="id"
            )
        geolocations = geolocations.select(
            (VKG + pl.col("id").cast(str)).alias("geolocation"),
            pl.format("POINT ({} {})", pl.col("longitude"), pl.col("latitude"))
            .cast(str)
            .alias("centroid"),
            geolocations.get_column("thoroughfare", default=pl.lit(None)).alias(
                "address"
            ),
            geolocations.get_column("post_name", default=pl.lit(None)).alias(
                "postal_name"
            ),
            geolocations.get_column("county", default=pl.lit(None)).alias("state"),
            geolocations.get_column("postcode", default=pl.lit(None))
            .cast(str)
            .alias("postal_code"),
            geolocations.get_column("country", default=pl.lit(country))
            .fill_null(country)
            .alias("country"),
        )
        m.expand("vkg-evse:GeoLocation", geolocations, graph=f"{VKG}{name}")

    if (p := Path(f"{path}/bnetza_operators_{dd}_{mm}_{yyyy}.csv")).exists():
        operator: pl.DataFrame = pl.read_csv(p)
        if challenge:
            operator = operator.filter(pl.col("id").is_in(operator_ids))
        operator = operator.select(
            (VKG + "bnetza_operator" + pl.col("id").cast(str).str.zfill(8)).alias("operator"),
            pl.col("operator").cast(str).alias("label"),
            operator.get_column("type", default=pl.lit("operator"))
            .map_elements(
                lambda x: "https://www.commoncoreontologies.org/ont00001006"
                if x == "operator"
                else pl.Null,
                return_dtype=pl.String,
            )
            .alias("role"),
        )
        m.expand("vkg-evse:Operator", operator, graph=f"{VKG}{name}")

    if (p := Path(f"{path}/bnetza_columns_{dd}_{mm}_{yyyy}.csv")).exists():
        columns: pl.DataFrame = pl.read_csv(p)
        if challenge:
            columns = columns.filter(pl.col("facility_id").is_in(facility_ids))
        column_ids = columns["id"].unique()
        columns = columns.select(
            (VKG + "bnetza_column" + pl.col("column_id").cast(str).str.zfill(8)).alias("column"),
            (VKG + "bnetza_facility" + pl.col("facility_id").cast(str).str.zfill(8)).alias("facility"),
            (VKG + pl.col("geolocation_id").cast(str)).alias("geolocation"),
            pl.col("display_name").cast(str).alias("ID"),
            pl.col("net_capacity").alias("max_power"),
            pl.col("commissioning_date").str.to_datetime().alias("commisioning"),
        )
        m.expand("vkg-evse:Column", columns, graph=f"{VKG}{name}")

    if (p := Path(f"{path}/bnetza_points_{dd}_{mm}_{yyyy}.csv")).exists():
        evse: pl.DataFrame = pl.read_csv(p)
        if challenge:
            evse = evse.filter(pl.col("facility_id").is_in(facility_ids))
        evse_ids = evse["id"].unique()
        evse = evse.select(
            (VKG + "bnetza_evse" + pl.col("id").cast(str).str.zfill(8)).alias("evse"),
            (VKG + "bnetza_column" + pl.col("column_id").cast(str).str.zfill(8)).alias("column"),
            pl.col("EVSE-ID").cast(str).alias("ID"),
            pl.col("Key").cast(str).alias("altID"),
        )
        m.expand("vkg-evse:EVSE", evse, graph=f"{VKG}{name}")

    if (p := Path(f"{path}/bnetza_compatibility_{dd}_{mm}_{yyyy}.csv")).exists():
        connections: pl.DataFrame = pl.read_csv(p)
        if challenge:
            connections = connections.filter(pl.col("evse_id").is_in(evse_ids))
        if (p := Path(f"{path}/bnetza_sockets_{dd}_{mm}_{yyyy}.csv")).exists():
            connections = connections.join(
                pl.read_csv(p), left_on="socket_id", right_on="id"
            ).select(
                (VKG + "bnetza_evse" + pl.col("point_id").cast(str).str.zfill(8)).alias("evse"),
                pl.col("pattern")
                .map_elements(map_plug_standards, return_dtype=pl.String)
                .alias("pattern"),
                pl.col("connector").map_elements(
                    map_coupling_method, return_dtype=pl.String
                ),
                pl.col("power").cast(float),
            )
            m.expand("vkg-evse:Connection", connections, graph=f"{VKG}{name}")