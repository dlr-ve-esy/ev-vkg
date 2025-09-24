import polars as pl
from datetime import datetime as dt


def restructure_datex2(data, name):
    new = {}
    date = dt.strptime(name.split("-")[1], "%Y%m%d").strftime("%Y-%m-%d")
    if (oadresses := data.get("addresses", None)) is not None:
        if oadresses.get_column("id", default=None) is not None:
            id_col = pl.col("id").cast(pl.String)
        else:
            id_col = pl.lit(None).alias("id")

        if oadresses.get_column("street_dirty", default=None) is not None:
            street_col = (
                pl.col("street_dirty")
                .cast(pl.String)
                .str.replace("Direccion: ", "")
                .alias("street")
            )
        elif oadresses.get_column("address_text", default=None) is not None:
            street_col = pl.col("address_text").cast(pl.String).alias("street")
        else:
            street_col = pl.lit(None).alias("street")

        if oadresses.get_column("city", default=None) is not None:
            postal_name_col = pl.col("city").cast(pl.String).alias("postal_name")
        else:
            postal_name_col = pl.lit(None).alias("postal_name")

        if oadresses.get_column("postcode", default=None) is not None:
            zip_code_col = pl.col("postcode").cast(pl.String).alias("zip_code")
        else:
            zip_code_col = pl.lit(None).alias("zip_code")

        if oadresses.get_column("country_code", default=None) is not None:
            country_col = pl.col("country_code").cast(pl.String).alias("country")
        else:
            country_col = pl.lit(None).alias("country")
        new["addresses"] = oadresses.select(
            id_col,
            street_col,
            pl.lit(None).alias("locator_designator"),
            pl.lit(None).alias("supplement"),
            postal_name_col,
            zip_code_col,
            pl.lit(None).alias("state"),
            country_col,
            oadresses.get_column("timeZone", default=pl.lit(None)).alias("time_zone"),
            pl.lit(date).alias("last_update"),
        )

    if (oconnections := data.get("compatibilities", None)) is not None:
        new["connections"] = oconnections.select(
            pl.col("point_id").alias("evse_id"),
            pl.lit(name).alias("source_id"),
            pl.col("connector_id"),
        )

    if (oconnectors := data.get("connectors", None)) is not None:
        new["connectors"] = oconnectors.select(
            pl.col("id"),
            pl.col("type").alias("standard"),
            oconnectors.get_column("format", default=pl.lit(None)).alias("coupling"),
            oconnectors.get_column("voltage", default=pl.lit(None)).alias(
                "max_voltage"
            ),
            oconnectors.get_column("current", default=pl.lit(None)).alias(
                "max_amperage"
            ),
            pl.col("max_power").alias("max_power"),
        )

    if (ocoords := data.get("coordinates", None)) is not None:
        new["spatial"] = ocoords.select(
            pl.col("id"),
            pl.col("lat").alias("latitude"),
            pl.col("lon").alias("longitude"),
        )

    if (ofacilities := data.get("facilities", None)) is not None:
        new["facilities"] = ofacilities.select(
            pl.col("id"),
            pl.lit(name).alias("source_id"),
            ofacilities.get_column("operator_id", default=pl.lit(None)).alias(
                "operator_id"
            ),
            pl.col("geolocation_id").alias("geolocation_id"),
            ofacilities.get_column("name", default=pl.lit(None)).alias("name"),
            pl.col("last_updated"),
            pl.lit(None).alias("time_zone"),
        )

    if (ooperators := data.get("operators", None)) is not None:
        new["operators"] = ooperators.select(
            pl.col("id"),
            ooperators.get_column("name", default=pl.lit(None)).alias("name"),
            pl.lit("operator").alias("type"),
        )

    if (opoints := data.get("points", None)) is not None:
        new["evse"] = opoints.select(
            pl.col("id"),
            pl.lit(name).alias("source_id"),
            pl.col("facility_id"),
            pl.lit(None).alias("geolocation_id"),
            opoints.get_column("external_id", default=pl.lit(None)).alias("evseid"),
            pl.lit(date).alias("last_updated"),
        )

    if (olocations := data.get("locations", None)) is not None:
        new["geolocations"] = olocations.select(
            pl.col("id"), pl.col("spatial_id"), pl.col("address_id")
        )

    return new
