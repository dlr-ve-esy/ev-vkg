from typing import Any, Dict, Tuple
import xml.etree.ElementTree as ET
import polars as pl
from zlib import crc32

NS = {
    "common": "http://datex2.eu/schema/3/common",
    "locationExtension": "http://datex2.eu/schema/3/locationExtension",
    "locationReferencing": "http://datex2.eu/schema/3/locationReferencing",
    "facilities": "http://datex2.eu/schema/3/facilities",
    "commonExtension": "http://datex2.eu/schema/3/commonExtension",
    "energyInfrastructure": "http://datex2.eu/schema/3/energyInfrastructure",
    "messageContainer": "http://datex2.eu/schema/3/messageContainer",
    "d2Payload": "http://datex2.eu/schema/3/d2Payload",
    "parking": "http://datex2.eu/schema/3/parking",
    "xsi": "http://datex2.eu/schema/3/XMLSchema-instance",
}


def get_value(element: ET.Element, tag: str) -> str | None:
    identifier = element.find(tag, NS)
    if identifier is not None:
        text = identifier.text
        if text is not None:
            if len(text) == 0:
                return None
        return text
    return None


def get_deep_value(element: ET.Element, tag: str) -> str | None:
    sub_element = element.find(tag, NS)
    if sub_element is not None:
        values = sub_element.find("common:values", NS)
        if values is not None:
            value = values.find("common:value", NS)
            if value is not None:
                text = value.text
                return text
    return None


def get_operating_hours(element: ET.Element) -> str | None:
    oh = element.find("facilities:operatingHours", NS)
    ohe = element.find("energyInfrastructure:operatingHours", NS)
    if oh is not None:
        if oh.text is None:
            category = list(oh.attrib.values())[0]
            if "OpenAllHours" in category:
                return "24h"
        else:
            return oh.text.strip()
    elif ohe is not None:
        if ohe.text is None:
            category = list(ohe.attrib.values())[0]
            if "OpenAllHours" in category:
                return "24h"
        else:
            return ohe.text.strip()

    return None


def get_street(element) -> str | None:
    address_line = element.find("locationExtension:addressLine", NS)
    if address_line is not None:
        text = get_deep_value(address_line, "locationExtension:text")
        if text is None:
            text = address_line.find("locationExtension:text", NS).text
        return text
    return None


def get_address_information(element: ET.Element) -> Dict[str, Any]:
    address: Dict[str, Any] = {}
    location_ref = element.find("facilities:locationReference", NS)
    if location_ref is not None:
        loc_extension = location_ref.find(
            "locationReferencing:_locationReferenceExtension", NS
        )
        if loc_extension is None:
            loc_extension = location_ref.find(
                "locationReferencing:_pointLocationExtension", NS
            )
        if loc_extension is not None:
            facility_location = loc_extension.find(
                "locationReferencing:facilityLocation", NS
            )
            if facility_location is None:
                facility_location = loc_extension.find(
                    "locationExtension:facilityLocation", NS
                )
            if facility_location is not None:
                tz_maybe = facility_location.find("locationExtension:timeZone", NS)
                tz_text = tz_maybe.text if tz_maybe is not None else None
                if tz_text is not None:
                    address["timeZone"] = tz_text
                address_maybe = facility_location.find("locationExtension:address", NS)
                if address_maybe is not None:
                    postcode_maybe = get_value(
                        address_maybe, "locationExtension:postcode"
                    )
                    if postcode_maybe is not None:
                        address["postcode"] = postcode_maybe
                    city_maybe = get_deep_value(address_maybe, "locationExtension:city")
                    if city_maybe is not None:
                        address["city"] = city_maybe
                    country_code_maybe = get_value(
                        address_maybe, "locationExtension:countryCode"
                    )
                    if country_code_maybe is not None:
                        address["country_code"] = country_code_maybe
                    street_maybe = get_street(address_maybe)
                    if street_maybe is not None:
                        address["street_dirty"] = street_maybe.strip().replace(
                            "Dirección: ", ""
                        )
    if_address = element.find(
        "energyInfrastructure:energyInfrastructureSiteAddress", NS
    )
    if if_address is not None:
        address_line = if_address.find("common:addressLineText", NS)
        if address_line is not None:
            if (al := address_line.find("common:value", NS)) is not None:
                address["address_text"] = al.text
    return address


def get_operator_information(element: ET.Element) -> Dict["str", Any]:
    operator: Dict["str", Any] = {}
    operator_maybe = element.find("facilities:operator", NS)
    if operator_maybe is not None:
        operator_id = operator_maybe.attrib["id"]
        if operator_id is not None:
            operator["id"] = operator_id
        sub_org = operator_maybe.find("facilities:subOrganisation", NS)
        if sub_org is not None:
            sub_id = get_deep_value(sub_org, "facilities:name")
            if sub_id is not None:
                operator["id"] = operator["id"] + "-" + sub_id
        name = get_deep_value(operator_maybe, "facilities:name")
        if name is not None:
            operator["name"] = name
        website = get_value(operator_maybe, "facilities:linkToGeneralInformation")
        if website is not None:
            operator["website"] = website
        org_number = get_value(operator_maybe, "facilities:nationalOrganisationNumber")
        if org_number is not None:
            operator["national_org_number"] = org_number
        vat_number = get_value(operator_maybe, "facilities:vatIdentificationNumber")
        if vat_number is not None:
            operator["vat_id_number"] = vat_number
        org_unit = element.find("facilities:organisationUnit", NS)
        if org_unit is not None:
            contact_info = org_unit.find("facilities:contactInformation", NS)
            if contact_info is not None:
                telephone_number = get_value(contact_info, "facilities:telephoneNumber")
                if telephone_number is not None:
                    operator["telephone_number"] = telephone_number
    else:
        operator_maybe = element.find("energyInfrastructure:energyProvider", NS)
        if operator_maybe is not None:
            operator_id = operator_maybe.attrib["id"]
            if operator_id is not None:
                operator["id"] = operator_id
            name = get_deep_value(operator_maybe, "facilities:name")
            if name is not None:
                operator["name"] = name
            last_updated = get_value(operator_maybe, "facilities:lastUpdated")
            if last_updated is not None:
                operator["last_updated"] = last_updated
            org_unit = operator_maybe.find("facilities:organisationUnit", NS)
            if org_unit is not None:
                contact_info = org_unit.find("facilities:contactInformation", NS)
                if contact_info is not None:
                    telephone_number = get_value(
                        contact_info, "facilities:telephoneNumber"
                    )
                    if telephone_number is not None:
                        operator["telephone_number"] = telephone_number
                    email = get_value(contact_info, "facilities:eMail")
                    if email is not None:
                        operator["email"] = email

    return operator


def get_coordinates(element: ET.Element) -> Tuple[float, float] | None:
    location_ref = element.find("facilities:locationReference", NS)
    # Most common approach
    if location_ref is not None:
        point_by_coords = location_ref.find(
            "locationReferencing:pointByCoordinates", NS
        )
        if point_by_coords is not None:
            coords = point_by_coords.find("locationReferencing:pointCoordinates", NS)
            if coords is not None:
                lat = get_value(coords, "locationReferencing:latitude")
                lon = get_value(coords, "locationReferencing:longitude")
                if (lat is not None) and (lon is not None):
                    return (float(lat), float(lon))
        coords_display = location_ref.find(
            "locationReferencing:coordinatesForDisplay", NS
        )
        if coords_display is not None:
            lat = get_value(coords_display, "locationReferencing:latitude")
            lon = get_value(coords_display, "locationReferencing:longitude")
            if (lat is not None) and (lon is not None):
                return (float(lat), float(lon))
    # LV has only coordiantes to the entrace
    entrance = element.find("energyInfrastructure:entrance", NS)
    if entrance is not None:
        loc_ref = entrance.find("locationReferencing:openlrPointLocationReference", NS)
        if loc_ref is not None:
            coords = loc_ref.find("locationReferencing:openlrCoordinates", NS)
            if coords is not None:
                actual_coords = loc_ref.find(
                    "locationReferencing:openlrCoordinates", NS
                )
                if actual_coords is not None:
                    lat = get_value(actual_coords, "locationReferencing:latitude")
                    lon = get_value(actual_coords, "locationReferencing:longitude")
                    if (lat is not None) and (lon is not None):
                        return (float(lat), float(lon))
    # CY: yet another take
    location = element.find("locationReferencing:location", NS)
    if location is not None:
        point_by_coords = location.find("locationReferencing:pointByCoordinates", NS)
        if point_by_coords is not None:
            coords = point_by_coords.find("locationReferencing:pointCoordinates", NS)
            if coords is not None:
                lat = get_value(coords, "common:latitude")
                lon = get_value(coords, "common:longitude")
                if (lat is not None) and (lon is not None):
                    return (float(lat), float(lon))
    return None


def parse_datex2_xml(filepath, country_code="XX"):
    tree = ET.parse(filepath)
    root = tree.getroot()

    # Parse Portugal
    table = root.find("energyInfrastructure:energyInfrastructureTable", NS)
    if table is None:
        table = root

    if (tt := root.find("messageContainer:payload", NS)) is not None:
        table = tt.find("energyInfrastructure:energyInfrastructureTable", NS)
    # case for newer versions of CY
    if (tt := root.find("common:payload", NS)) is not None:
        table = tt.find("energyInfrastructure:energyInfrastructureTable", NS)

    operators = {}
    facilities = []
    addresses = {}
    locations = []
    coordinates = {}
    stations = []
    points = []
    connectors = {}
    compatibilities = []

    if table is not None:
        for site in table.findall("energyInfrastructure:energyInfrastructureSite", NS):
            facility = {}
            location: Dict[str, Any] = {}
            if "id" in site.attrib:
                facility_id = site.attrib["id"].strip()
            else:
                facility_id = get_value(
                    site, "energyInfrastructure:energyInfrastructureSiteReference"
                )
            facility["id"] = facility_id
            name = get_deep_value(site, "facilities:name")
            if name is not None:
                facility["name"] = name
            else:
                name = site.find(
                    "energyInfrastructure:energyInfrastructureSiteName", NS
                )
                if name is not None:
                    txt = name.find("common:value", NS)
                    if txt is not None:
                        if (tx := txt.text) is not None:
                            facility["name"] = tx.strip()
            cp_no = site.find("energyInfrastructure:numberOfChargingPoints", NS)
            if cp_no is not None:
                if (tx := cp_no.text) is not None:
                    facility["cp_number"] = tx.strip()
            facility["external_identifier"] = get_value(
                site, "facilities:externalIdentifier"
            )
            facility["last_updated"] = get_value(site, "facilities:lastUpdated")
            oh = get_operating_hours(site)
            if oh is not None:
                facility["opening_hours"] = get_operating_hours(site)

            address = get_address_information(site)
            if len(address) > 0:
                ad_hash = int(crc32("".join((address.values())).encode("utf8")))
                if ad_hash not in addresses:
                    ad_temp: Dict[str, Any] = {}
                    ad_temp["id"] = ad_hash
                    ad_temp.update(address)
                    cc = ad_temp.get("country_code", None)
                    if (cc is None) | (cc == "XX"):
                        ad_temp["country_code"] = country_code
                    addresses[ad_hash] = ad_temp
                location["address_id"] = ad_hash
            else:
                location["address_id"] = None
                ad_hash = 0

            coord_maybe = get_coordinates(site)
            if coord_maybe is not None:
                coordinate_hash = int(
                    str(int(coord_maybe[0] * 100000))
                    + str(int(coord_maybe[1] * 100000)).replace("-", "1")
                )
                if coordinate_hash not in coordinates:
                    coordinates[coordinate_hash] = coord_maybe
                location["spatial_id"] = coordinate_hash
            else:
                location["spatial_id"] = None
                coordinate_hash = 0
            location["id"] = (
                "A" + str(ad_hash).zfill(6)[0:6] + "S" + str(coordinate_hash)
            )
            facility["geolocation_id"] = location["id"]
            for st in site.findall(
                "energyInfrastructure:energyInfrastructureStation", NS
            ):
                station: Dict[str, str | None] = {}
                station_id = st.attrib["id"].strip()
                station["id"] = station_id
                station["facility_id"] = facility_id
                associated_facility = st.find("facilities:associatedFacility", NS)
                if associated_facility is not None:
                    facility_type = associated_facility.find("facilities:type", NS)
                    if facility_type is not None:
                        facility["associated_facility"] = facility_type.text
                for pt in st.findall("energyInfrastructure:refillPoint", NS):
                    point: Dict[str, str | None] = {}
                    point_id = pt.attrib["id"].strip()
                    point["id"] = point_id
                    external_id = pt.find("facilities:externalIdentifier", NS)
                    if external_id is not None:
                        point["external_id"] = external_id.text
                    point["facility_id"] = facility_id
                    # TODO: Rates, usage type
                    for conn in pt.findall("energyInfrastructure:connector", NS):
                        connector = {}
                        connector["type"] = get_value(
                            conn, "energyInfrastructure:connectorType"
                        )
                        _format = get_value(
                            conn, "energyInfrastructure:connectorFormat"
                        )
                        connector["max_power"] = get_value(
                            conn, "energyInfrastructure:maxPowerAtSocket"
                        )
                        if _format in ["cableMode2", "cableMode3", "otherCable"]:
                            connector["format"] = "cable"
                        elif _format == "socket":
                            connector["format"] = "socket"
                        voltage = get_value(conn, "energyInfrastructure:voltage")
                        if voltage == "maxPowerAtSocket.0":
                            # error in portugal data
                            voltage = "375"
                        connector["voltage"] = voltage
                        connector["current"] = get_value(
                            conn, "energyInfrastructure:maximumCurrent"
                        )
                        cn_hash = int(
                            crc32(
                                "".join(
                                    [v for v in connector.values() if v is not None]
                                ).encode("utf8")
                            )
                        )
                        if cn_hash not in connectors:
                            cn_tmp: Dict[str, Any] = {}
                            cn_tmp["id"] = cn_hash
                            cn_tmp.update(connector)
                            connectors[cn_hash] = cn_tmp
                        compatibilities.append((point_id, cn_hash))

                    points.append(point)
                # TODO: Auth methods

                st_operator = get_operator_information(st)
                if len(st_operator) == 0:
                    st_operator = get_operator_information(site)
                if "id" in st_operator:
                    if str(st_operator["id"]).strip() == "1":
                        st_operator["id"] = int(
                            crc32(st_operator["name"].encode("utf8"))
                        )
                    if st_operator["id"] not in operators:
                        operators[st_operator["id"]] = st_operator
                    facility["operator_id"] = st_operator["id"]
                # stations.append(station)

            operator = get_operator_information(site)
            if "id" in operator:
                if str(operator["id"]).strip() == "1":
                    operator["id"] = int(crc32(operator["name"].encode("utf8")))
                if operator["id"] not in operators:
                    operators[operator["id"]] = operator
                facility["operator_id"] = operator["id"]
            facilities.append(facility)
            locations.append(location)

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
    if len(locations) > 0:
        data["locations"] = pl.DataFrame(locations, infer_schema_length=None).unique(
            maintain_order=True
        )
    if len(stations) > 0:
        data["stations"] = pl.DataFrame(stations, infer_schema_length=None)
    if len(points) > 0:
        data["points"] = pl.DataFrame(points, infer_schema_length=None)
    if len(connectors) > 0:
        data["connectors"] = pl.DataFrame(
            list(connectors.values()), infer_schema_length=None
        )
    if len(compatibilities) > 0:
        data["compatibilities"] = pl.DataFrame(
            [{"point_id": cmp[0], "connector_id": cmp[1]} for cmp in compatibilities],
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
