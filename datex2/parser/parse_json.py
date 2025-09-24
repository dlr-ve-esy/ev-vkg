from typing import Any, Dict
import json
import polars as pl
from pathlib import Path
from zlib import crc32
from datetime import datetime


def get_address_information(element: Dict) -> Dict[str, Any]:
    address: Dict[str, Any] = {}
    for line in element.get("addressLine", []):
        if line.get("type", {}).get("value", "") == "STREET":
            address["street"] = (
                line.get("text", {})
                .get("values", {})
                .get("value", [{}])[0]
                .get("value", None)
            )
        if line.get("type", {}).get("value", "") == "HOUSE_NUMBER":
            address["locator_designator"] = (
                line.get("text", {})
                .get("values", {})
                .get("value", [{}])[0]
                .get("value", None)
            )
    address["postal_name"] = (
        element.get("city", {})
        .get("values", {})
        .get("value", [{}])[0]
        .get("value", None)
    )
    address["zip_code"] = element.get("postcode", None)
    address["country"] = element.get("countryCode", None)
    return address


def get_coordinates(element):
    if (cfd := element.get("coordinatesForDisplay", None)) is not None:
        coord_source = cfd
        return (
            float(coord_source.get("longitude", None)),
            float(coord_source.get("latitude", None)),
        )
    elif (cfd := element.get("pointByCoordinates", None)) is not None:
        coord_source = cfd.get("pointCoordinates", {})
        return (
            float(coord_source.get("longitude", None)),
            float(coord_source.get("latitude", None)),
        )
    else:
        return None


def parse_datex2_json(filepath: str, country_code="XX"):
    with open(filepath, "r") as f:
        document = json.load(f)

    operators = {}
    facilities = []
    addresses = {}
    geolocations = {}
    coordinates = {}
    columns = []
    evses = []
    connectors = {}
    connections = []

    for site in document["energyInfrastructureTable"][0]["energyInfrastructureSite"]:
        facility = {}
        location: Dict[str, Any] = {}
        facility["id"] = site.get("id", None)
        facility["name"] = (
            site.get("name", {})
            .get("values", {})
            .get("value", [{}])[0]
            .get("value", None)
        )
        facility["last_updated"] = datetime.fromtimestamp(
            site.get("lastUpdated", datetime.now().timestamp() * 1000) / 1000
        ).strftime("%Y-%m-%d %H:%M:%S")

        operator = {}
        operator_source = site.get("operator", {})
        operator_id = operator_source.get("id", None)
        operator["id"] = operator_id
        operator["name"] = (
            operator_source.get("name", {})
            .get("values", {})
            .get("value", [{}])[0]
            .get("value", None)
        )
        operator["type"] = "operator"

        facility["operator_id"] = operator_id

        geolocation: Dict[str, Any] = {}
        geolocation_source = site.get("locationReference", {})

        address_source = (
            geolocation_source.get("_LocationReferenceExtension", {})
            .get("facilityLocation", {})
            .get("address", {})
        )
        address = get_address_information(address_source)
        if len(address) > 0:
            ad_hash = int(crc32("".join((address.values())).encode("utf8")))
            if ad_hash not in addresses:
                address["last_update"] = facility["last_updated"]
                ad_temp = {}
                ad_temp["id"] = ad_hash
                ad_temp.update(address)
                cc = ad_temp.get("country_code", None)
                if (cc is None) | (cc == "XX"):
                    ad_temp["country_code"] = country_code
                addresses[ad_hash] = ad_temp
            geolocation["address_id"] = ad_hash
        else:
            geolocation["address_id"] = None
            ad_hash = 0

        coord_maybe = get_coordinates(geolocation_source)
        if coord_maybe is not None:
            coord = tuple(coord_maybe)
            coordinate_hash = int(
                str(int(coord_maybe[0] * 100000))
                + str(int(coord_maybe[1] * 100000)).replace("-", "1")
            )
            if coordinate_hash not in coordinates:
                coordinates[coordinate_hash] = coord_maybe
            geolocation["spatial_id"] = coordinate_hash
        else:
            geolocation["spatial_id"] = None
            coordinate_hash = 0
        geolocation["id"] = (
            "A" + str(ad_hash).zfill(6)[0:6] + "S" + str(coordinate_hash)
        )
        if geolocation["id"] not in geolocations:
            geolocations[geolocation["id"]] = geolocation
        facility["geolocation_id"] = geolocation["id"]
        facilities.append(facility)
        if operator["id"] not in operators:
            operators[operator["id"]] = operator

        for station_source in site.get("energyInfrastructureStation"):
            column = {}
            station_id = station_source.get("id", None)
            column["id"] = station_id
            column["facility_id"] = facility["id"]
            geolocation_source = station_source.get("locationReference", {})
            coord_maybe = get_coordinates(geolocation_source)
            columns.append(column)
            if coord_maybe is not None:
                coord = tuple(coord_maybe)
                coordinate_hash = int(
                    str(int(coord_maybe[0] * 100000))
                    + str(int(coord_maybe[1] * 100000)).replace("-", "1")
                )
                if coordinate_hash not in coordinates:
                    coordinates[coordinate_hash] = coord_maybe
                geolocation = {}
                geolocation["address_id"] = ad_hash
                geolocation["spatial_id"] = coordinate_hash
                geolocation["id"] = (
                    "A" + str(ad_hash).zfill(6)[0:6] + "S" + str(coordinate_hash)
                )
                column["geolocation_id"] = geolocation["id"]
                if geolocation["id"] not in geolocations:
                    geolocations[geolocation["id"]] = geolocation
            for point in station_source.get("refillPoint", []):
                evse = {}
                evse_id = point.get("id", None)
                evse["id"] = evse_id
                evse["column_id"] = column["id"]
                evse["last_update"] = datetime.fromtimestamp(
                    int(site.get("version", datetime.now().timestamp() * 1000)) / 1000
                ).strftime("%Y-%m-%d %H:%M:%S")
                evses.append(evse)
                for conn in point.get("connector", []):
                    connector = {}
                    connector["type"] = conn.get("connectorType", {}).get("value", None)
                    connector["max_power"] = conn.get("maxPowerAtSocket", None)
                    cn_hash = int(
                        crc32(
                            "".join(
                                [str(v) for v in connector.values() if v is not None]
                            ).encode("utf8")
                        )
                    )
                    if cn_hash not in connectors:
                        cn_tmp: Dict[str, Any] = {}
                        cn_tmp["id"] = cn_hash
                        cn_tmp.update(connector)
                        connectors[cn_hash] = cn_tmp
                    connections.append((evse_id, cn_hash))

    data = {}

    if len(operators) > 0:
        data["operators"] = pl.DataFrame(
            list(operators.values()), infer_schema_length=None
        )
    if len(facilities) > 0:
        data["facilities"] = pl.DataFrame(facilities, infer_schema_length=None)
    if len(addresses) > 0:
        data["addresses"] = pl.DataFrame(
            list(addresses.values()), infer_schema_length=None
        )
    if len(geolocations) > 0:
        data["geolocations"] = pl.DataFrame(
            list(geolocations.values()), infer_schema_length=None
        ).unique(maintain_order=True)
    if len(columns) > 0:
        data["columns"] = pl.DataFrame(columns, infer_schema_length=None)
    if len(evses) > 0:
        data["evse"] = pl.DataFrame(evses, infer_schema_length=None)
    if len(connectors) > 0:
        connectors_df = pl.DataFrame(
            list(connectors.values()), infer_schema_length=None
        )
        data["connectors"] = connectors_df.with_columns(
            pl.col("type")
            .str.replace("TESLA_CONNECTOR_EUROPE", "TESLA")
            .str.replace_all("_", "")
        )
    if len(connections) > 0:
        data["connections"] = pl.DataFrame(
            [{"evse_id": cmp[0], "connector_id": cmp[1]} for cmp in connections],
            infer_schema_length=None,
        )
    if len(coordinates) > 0:
        data["coordinates"] = pl.DataFrame(
            [
                {"id": i, "lat": cmp[0], "lon": cmp[1]}
                for (i, cmp) in coordinates.items()
            ],
            infer_schema_length=None,
        )

    return data
