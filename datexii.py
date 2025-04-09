from glob import glob
from pathlib import Path
from typing import List, Tuple
import polars as pl
from maplib import Mapping, Prefix, Template, Parameter, Variable, RDFType, Triple, a


paths: List[Path] = [Path(f) for f in glob("operational/*")]
mappings: List[Tuple[str, str]] = [(m.name, m.as_posix()) for m in paths]

namespace = "https://gitlab.dlr.de/datex2#"

def main() -> Mapping:

    
    prefix = Prefix("vkg", namespace)
    rdfs = Prefix("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
    chio = Prefix("chio", "https://dlr-ve-esy.github.io/charging_ontology/")
    cco = Prefix("cco", "https://www.commoncoreontologies.org/")
    bfo =  Prefix("bfo", "http://purl.obolibrary.org/obo/")
    with open("templates/evse.stottr", "r") as d:
        template = d.read()
    m = Mapping([template])
   
    for name, path in mappings:
        pl.Config.set_fmt_str_lengths(150)
        if (p := Path(f"{path}/facility.csv")).exists():
            facility: pl.DataFrame  = pl.read_csv(p).select(
                (namespace + pl.col("id").cast(str)).alias("facility"),
                (namespace + pl.col("operator_id").cast(str)).alias("operator"),
                (namespace + pl.col("address_id").cast(str).alias("address"))
            )    
        if (p := Path(f"{path}/evses.csv")).exists():
            evse: pl.DataFrame = pl.read_csv(p).select(
                (namespace + pl.col("id").cast(str)).alias("evse"),
                (namespace + pl.col("facility_id").cast(str)).alias("facility"),
                pl.col("evseid").cast(str).alias("label")
            )
            
            m.expand("evse:EVSETemplate", evse)
    return m


if __name__ == "__main__":
    m = main()

    print(m.query("""
PREFIX vkg:<https://gitlab.dlr.de/datex2#>
PREFIX chio:<https://dlr-ve-esy.github.io/charging_ontology/>
PREFIX bfo:<http://purl.obolibrary.org/obo/>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
SELECT ?e ?f ?l WHERE {
    ?e a chio:CHIO_00000016 .
    ?e bfo:BFO_0000176 ?f .
    ?e rdfs:label ?l
}
"""))
