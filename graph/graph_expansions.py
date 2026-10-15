from pathlib import Path
from typing import Optional
import polars as pl
from maplib import Mapping
import re
import datetime

CHIO = "https://dlr-ve-esy.github.io/charging-ontology/"
VKG = "https://gitlab.dlr.de/vkg#"

CHALLENGE_MODE = True


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
        case (
            "iec62196t2"
            | "type2"
            | "type_2"
            | "iec_62196_t2"
            | "cee5"
            | "mennekes"
            | "teslaConnectorEurope"
        ):
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
            out = f"{CHIO}CHIO_00000015"
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
    country_filter=[],
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
        facility = pl.read_csv(p)
        if challenge:
            facility = facility.sample(5)
        if (p := Path(f"{path}/geolocations.csv")).exists():
            geolocations: pl.DataFrame = pl.read_csv(p)
            if (p := Path(f"{path}/spatial.csv")).exists():
                geolocations = geolocations.join(
                    pl.read_csv(p),
                    left_on="spatial_id",
                    right_on="id",
                    nulls_equal=True,
                    how="left",
                )
            elif (p := Path(f"{path}/coordinates.csv")).exists():
                geolocations = geolocations.join(
                    pl.read_csv(p),
                    left_on="spatial_id",
                    right_on="id",
                    nulls_equal=True,
                    how="left",
                )
            if (p := Path(f"{path}/addresses.csv")).exists():
                geolocations = geolocations.join(
                    pl.read_csv(p, infer_schema_length=None),
                    left_on="address_id",
                    right_on="id",
                    nulls_equal=True,
                    how="left",
                )

            if len(country_filter) > 0:
                geolocations = geolocations.filter(
                    pl.col("country").is_in(country_filter)
                )

                geo_ids = geolocations["id"].unique().to_list()
                facility = facility.filter(pl.col("geolocation_id").is_in(geo_ids))

            geolocations = geolocations.select(
                (VKG + pl.col("id").cast(str)).alias("geolocation"),
                pl.format("POINT ({} {})", pl.col("longitude"), pl.col("latitude"))
                .cast(str)
                .alias("centroid"),
                geolocations.get_column("street", default=pl.lit(None)).alias(
                    "address"
                ),
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

        operator_ids = facility["operator_id"].unique()
        facility_ids = facility["id"].unique()
        facility = facility.select(
            (VKG + pl.col("id").cast(str)).alias("facility"),
            (VKG + pl.col("operator_id").cast(str)).alias("operator"),
            (VKG + pl.col("geolocation_id").cast(str)).alias("geolocation"),
            pl.col("id").cast(str).alias("ID"),
        )
        m.expand("vkg-evse:Facility", facility, graph=f"{VKG}{name}")

    if (p := Path(f"{path}/operators.csv")).exists():
        operator: pl.DataFrame = pl.read_csv(p)
        operator = operator.filter(pl.col("id").is_in(operator_ids))
        operator = operator.select(
            (VKG + pl.col("id").cast(str)).alias("operator"),
            pl.col("name").cast(str).alias("label"),
            pl.col("id").cast(str).alias("ID"),
            pl.col("type")
            .map_elements(
                lambda x: (
                    "https://www.commoncoreontologies.org/ont00001006"
                    if x == "operator"
                    else pl.Null
                ),
                return_dtype=pl.String,
            )
            .alias("role"),
        ).drop_nulls(subset="operator")
        m.expand("vkg-evse:Operator", operator, graph=f"{VKG}{name}")
    if (p := Path(f"{path}/columns.csv")).exists():
        columns: pl.DataFrame = pl.read_csv(p, infer_schema_length=None)
        columns = columns.filter(pl.col("facility_id").is_in(facility_ids))
        column_ids = columns["id"].unique()
        challenge_ids = column_ids
        challenge_identifier = "column_id"
        columns = columns.select(
            (VKG + pl.col("id").cast(str)).alias("column"),
            (VKG + pl.col("facility_id").cast(str)).alias("facility"),
            (VKG + pl.col("geolocation_id").cast(str)).alias("geolocation"),
        )

        m.expand("vkg-evse:Column", columns, graph=f"{VKG}{name}")

        evse_fk = (VKG + pl.col("column_id").cast(str)).alias("column")
        evse_expansion_template = "vkg-evse:EVSE"
    else:
        challenge_ids = facility_ids
        challenge_identifier = "facility_id"
        evse_fk = (VKG + pl.col("facility_id").cast(str)).alias("facility")
        evse_expansion_template = "vkg-evse:EVSEColumn"
    if (p := Path(f"{path}/evse.csv")).exists():
        evse: pl.DataFrame = pl.read_csv(p)
        evse = evse.filter(pl.col(challenge_identifier).is_in(challenge_ids))
        evse_ids = evse["id"].unique()
        evse = evse.select(
            (VKG + pl.col("id").cast(str)).alias("evse"),
            evse_fk,
            pl.col("id").cast(str).alias("ID"),
            evse.get_column("evseid", default=pl.lit(None)).cast(str).alias("altID"),
        )
        m.expand(evse_expansion_template, evse, graph=f"{VKG}{name}")

    if (p := Path(f"{path}/connections.csv")).exists():
        connections: pl.DataFrame = pl.read_csv(p)
        connections = connections.filter(pl.col("evse_id").is_in(evse_ids))
        if (p := Path(f"{path}/connectors.csv")).exists():
            connections = connections.join(
                pl.read_csv(p),
                left_on="connector_id",
                right_on="id",
                nulls_equal=True,
                how="left",
            ).with_columns(
                connections.get_column("coupling", default=pl.lit("connector")).alias(
                    "coupling"
                )
            )
            connections = connections.select(
                (VKG + pl.col("evse_id").cast(str)).alias("evse"),
                pl.col("standard")
                .map_elements(map_plug_standards, return_dtype=pl.String)
                .alias("pattern"),
                pl.col("coupling").map_elements(
                    map_coupling_method, return_dtype=pl.String
                ),
                connections.get_column("max_voltage", default=pl.lit(None))
                .cast(float)
                .alias("max_voltage"),
                connections.get_column("max_amperage", default=pl.lit(None))
                .cast(float)
                .alias("max_amperage"),
                connections.get_column("max_power", default=pl.lit(None))
                .cast(float)
                .alias("max_power"),
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

    def facility_iri(id):
        return VKG + "bnetza_facility" + pl.col(id).cast(str).str.zfill(8)

    def operator_iri(id):
        return VKG + "bnetza_operator" + pl.col(id).cast(str).str.zfill(8)

    def geolocation_iri(id):
        return VKG + "bnetza_operator" + pl.col(id).cast(str).str.zfill(8)

    def column_iri(id):
        return VKG + "bnetza_column" + pl.col(id).cast(str).str.zfill(8)

    def evse_iri(id):
        return VKG + "bnetza_evse" + pl.col(id).cast(str).str.zfill(8)

    if (p := Path(f"{path}/bnetza_charging_facilities_{dd}_{mm}_{yyyy}.csv")).exists():
        facility: pl.DataFrame = pl.read_csv(p)
        if challenge:
            facility = facility.sample(5)
        geo_ids = facility["geolocation_id"].unique()
        operator_ids = facility["operator_id"].unique()
        facility_ids = facility["id"].unique()

        facility = facility.select(
            (facility_iri("id")).alias("facility"),
            (operator_iri("operator_id")).alias("operator"),
            (geolocation_iri("geolocation_id")).alias("geolocation"),
            pl.col("id").cast(str).alias("ID"),
        )
        m.expand("vkg-evse:Facility", facility, graph=f"{VKG}{name}")

    if (p := Path(f"{path}/bnetza_geolocations_{dd}_{mm}_{yyyy}.csv")).exists():
        geolocations: pl.DataFrame = pl.read_csv(p)
        if challenge:
            geolocations = geolocations.filter(pl.col("id").is_in(geo_ids))
        if (p := Path(f"{path}/bnetza_coordinates_{dd}_{mm}_{yyyy}.csv")).exists():
            geolocations = geolocations.join(
                pl.read_csv(p),
                left_on="coordinate_id",
                right_on="id",
                nulls_equal=True,
                how="left",
            )
        if (p := Path(f"{path}/addresses.csv")).exists():
            geolocations = geolocations.join(
                pl.read_csv(p),
                left_on="address_id",
                right_on="id",
                nulls_equal=True,
                how="left",
            )
        geolocations = geolocations.select(
            (geolocation_iri("id")).alias("geolocation"),
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
        operator = operator.with_columns(
            operator.get_column("type", default=pl.lit("operator")).alias("type")
        )
        if challenge:
            operator = operator.filter(pl.col("id").is_in(operator_ids))
        operator = operator.select(
            (operator_iri("id")).alias("operator"),
            pl.col("operator").cast(str).alias("label"),
            pl.col("type")
            .map_elements(
                lambda x: (
                    "https://www.commoncoreontologies.org/ont00001006"
                    if x == "operator"
                    else pl.Null
                ),
                return_dtype=pl.String,
            )
            .alias("role"),
        )
        m.expand("vkg-evse:Operator", operator, graph=f"{VKG}{name}")

    if (p := Path(f"{path}/bnetza_charging_columns_{dd}_{mm}_{yyyy}.csv")).exists():
        columns: pl.DataFrame = pl.read_csv(p)
        if challenge:
            columns = columns.filter(pl.col("facility_id").is_in(facility_ids))
        column_ids = columns["id"].unique()
        columns = columns.select(
            (column_iri("id")).alias("column"),
            (facility_iri("facility_id")).alias("facility"),
            (geolocation_iri("geolocation_id")).alias("geolocation"),
            pl.col("display_name").cast(str).alias("ID"),
            pl.col("net_capacity").fill_null(0.0).fill_nan(0.0).alias("max_power"),
            pl.col("commissioning_date")
            .cast(str)
            .alias("commisioning"),  # datetimes currently break the model
        )
        m.expand("vkg-evse:Column", columns, graph=f"{VKG}{name}")

    if (p := Path(f"{path}/bnetza_charging_points_{dd}_{mm}_{yyyy}.csv")).exists():
        evse: pl.DataFrame = pl.read_csv(p)
        if challenge:
            evse = evse.filter(pl.col("facility_id").is_in(facility_ids))
        evse_ids = evse["id"].unique()
        evse = evse.select(
            (evse_iri("id")).alias("evse"),
            (column_iri("column_id")).alias("column"),
            pl.col("EVSE-ID").cast(str).alias("ID"),
            pl.col("Key").cast(str).alias("altID"),
        )
        m.expand("vkg-evse:EVSE", evse, graph=f"{VKG}{name}")

    if (
        p := Path(f"{path}/bnetza_charging_compatibility_{dd}_{mm}_{yyyy}.csv")
    ).exists():
        connections: pl.DataFrame = pl.read_csv(p)
        if challenge:
            connections = connections.filter(pl.col("evse_id").is_in(evse_ids))
        if (p := Path(f"{path}/bnetza_charging_sockets_{dd}_{mm}_{yyyy}.csv")).exists():
            connections = connections.join(
                pl.read_csv(p),
                left_on="socket_id",
                right_on="id",
                nulls_equal=True,
                how="left",
            ).select(
                (evse_iri("point_id")).alias("evse"),
                pl.col("pattern")
                .map_elements(map_plug_standards, return_dtype=pl.String)
                .alias("pattern"),
                pl.col("connector")
                .map_elements(map_coupling_method, return_dtype=pl.String)
                .alias("coupling"),
                pl.col("power")
                .cast(float)
                .fill_null(0.0)
                .fill_nan(0.0)
                .mul(1000)
                .alias("max_power"),
            )
            m.expand("vkg-evse:Connection", connections, graph=f"{VKG}{name}")
