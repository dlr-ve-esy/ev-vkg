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
        template = d.read()
    m = Mapping([template])
   
    for name, path in mappings:
        pl.Config.set_fmt_str_lengths(150)
        if (p := Path(f"{path}/facility.csv")).exists():
            facility: pl.DataFrame  = pl.read_csv(p).select(
                (namespace + pl.col("id").cast(str)).alias("facility"),
                (namespace + pl.col("operator_id").cast(str)).alias("operator"),
                (namespace + pl.col("address_id").cast(str).alias("address")),
                pl.col("id").cast(str).alias("ID"),
            )    
        if (p := Path(f"{path}/evses.csv")).exists():
            evse: pl.DataFrame = pl.read_csv(p).select(
                (namespace + pl.col("id").cast(str)).alias("evse"),
                (namespace + pl.col("facility_id").cast(str)).alias("facility"),
                pl.col("id").cast(str).alias("ID"),
                pl.col("evseid").cast(str).alias("altID")
            )

            m.expand("vkg:EVSE", evse)
    return m


if __name__ == "__main__":
    m = main()

    print(m.query("""
PREFIX vkg:<https://gitlab.dlr.de/vkg#>
PREFIX chio:<https://dlr-ve-esy.github.io/charging_ontology/>
PREFIX cco:<https://www.commoncoreontologies.org/>
PREFIX bfo:<http://purl.obolibrary.org/obo/>
PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?e ?f ?l WHERE {
    ?e a chio:CHIO_00000016 .
    ?e bfo:BFO_0000176 ?f .
    ?e cco:ont00001879 ?id .
    ?id rdf:value ?l
}
"""))
