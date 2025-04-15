from glob import glob
from pathlib import Path
from typing import List, Tuple
import polars as pl
from maplib import Mapping

paths: List[Path] = [Path(f) for f in glob("operational/*")]
mappings: List[Tuple[str, str]] = [(m.name, m.as_posix()) for m in paths]

namespace = "https://gitlab.dlr.de/vkg#"


def main() -> Mapping:
    with open("templates/evse.stottr", "r") as d:
        vkg_evse = d.read()
    with open("templates/common.stottr", "r") as d:
        vkg_common = d.read()
    m = Mapping([vkg_common, vkg_evse])

    for name, path in mappings:
        country: str = name.split("-")[0]
        pl.Config.set_fmt_str_lengths(150)
        if (p := Path(f"{path}/geolocations.csv")).exists():
            geolocations: pl.DataFrame = pl.read_csv(p)
            if (p := Path(f"{path}/spatial.csv")).exists():
                geolocations = geolocations.join(
                    pl.read_csv(p), left_on="spatial_id", right_on="id"
                )
            if (p := Path(f"{path}/addresses.csv")).exists():
                geolocations = geolocations.join(
                    pl.read_csv(p), left_on="address_id", right_on="id"
                )
            geolocations = geolocations.select(
                (namespace + pl.col("id").cast(str)).alias("geolocation"),
                pl.format("POINT ({} {})", pl.col("longitude"), pl.col("latitude"))
                .cast(str)
                .alias("centroid"),
                geolocations.get_column("street", default=pl.lit(None)).alias("street"),
                geolocations.get_column("postal_name", default=pl.lit(None)).alias(
                    "postal_name"
                ),
                geolocations.get_column("state", default=pl.lit(None)).alias("state"),
                geolocations.get_column("country", default=pl.lit(country)).alias(
                    "country"
                ),
            )
            m.expand("vkg-evse:GeoLocation", geolocations, graph=f"{namespace}{name}")

        if (p := Path(f"{path}/facilities.csv")).exists():
            facility: pl.DataFrame = pl.read_csv(p).select(
                (namespace + pl.col("id").cast(str)).alias("facility"),
                (namespace + pl.col("operator_id").cast(str)).alias("operator"),
                (namespace + pl.col("geolocation_id").cast(str)).alias("geolocation"),
                pl.col("id").cast(str).alias("ID"),
            )
            m.expand("vkg-evse:Facility", facility, graph=f"{namespace}{name}")
        if (p := Path(f"{path}/operators.csv")).exists():
            operator: pl.DataFrame = pl.read_csv(p)
            operator = operator.select(
                (namespace + pl.col("id").cast(str)).alias("operator"),
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
            m.expand("vkg-evse:Operator", operator, graph=f"{namespace}{name}")
        if (p := Path(f"{path}/evses.csv")).exists():
            evse: pl.DataFrame = pl.read_csv(p).select(
                (namespace + pl.col("id").cast(str)).alias("evse"),
                (namespace + pl.col("facility_id").cast(str)).alias("facility"),
                pl.col("id").cast(str).alias("ID"),
                pl.col("evseid").cast(str).alias("altID"),
            )

            m.expand("vkg-evse:EVSE", evse, graph=f"{namespace}{name}")
    return m


if __name__ == "__main__":
    m = main()

    print(
        m.query(
            """
PREFIX vkg:<https://gitlab.dlr.de/vkg#>
PREFIX chio:<https://dlr-ve-esy.github.io/charging_ontology/>
PREFIX cco:<https://www.commoncoreontologies.org/>
PREFIX bfo:<http://purl.obolibrary.org/obo/>
PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dbo:<https://dbpedia.org/ontology/>

SELECT ?a ?b ?c WHERE {
    ?a rdf:type chio:CHIO_00000004 .
    ?a bfo:BFO_0000171+ ?b .
    ?b dbo:iso31661Code ?c .
}
""",
            graph=f"{namespace}PT-20250116-MOBIE-DATEXII",
        )
    )
