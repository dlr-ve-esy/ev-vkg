from glob import glob
from pathlib import Path
from typing import List, Tuple
import polars as pl
from maplib import Mapping, Prefix, Template, Parameter, Variable, RDFType, Triple, a


paths: List[Path] = [Path(f) for f in glob("operational/*")]
mappings: List[Tuple[str, str]] = [(m.name, m.as_posix()) for m in paths]

namespace = "https://gitlab.dlr.de/datex2#"

def main() -> Mapping:

    
    m = Mapping()
    for name, path in mappings:
        pl.Config.set_fmt_str_lengths(150)
        if (p := Path(f"{path}/evses.csv")).exists():
            raw: pl.DataFrame = pl.read_csv(p)
            
            prefix = Prefix("vkg", namespace)
            rdfs = Prefix("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
            chio = Prefix("chio", "https://dlr-ve-esy.github.io/charging_ontology/")
            cco = Prefix("cco", "https://www.commoncoreontologies.org/")
            bfo =  Prefix("bfo", "http://purl.obolibrary.org/obo/")

            evse = raw.select(
                (namespace + pl.col("id").cast(str)).alias("evse"),
                (namespace + pl.col("facility_id").cast(str)).alias("facility"),
                pl.col("evseid").alias("label")
            )
            evse_var = Variable("evse")
            facility_var = Variable("facility")
            label_var = Variable("label")
    
            evse_template = Template(
                iri= prefix.suf("EVSETemplate"),
                parameters= [
                    Parameter(variable=evse_var, rdf_type=RDFType.IRI()),
                    Parameter(variable=facility_var, rdf_type=RDFType.IRI()),
                    Parameter(variable=label_var, optional=True)
                ],
                instances= [
                    Triple(evse_var, a(), chio.suf("CHIO_00000016")),
                    Triple(evse_var, bfo.suf("BFO_0000176"), facility_var),
                    Triple(
                        evse_var, 
                        rdfs.suf("label"), 
                        label_var)
                ]
            )
            m.expand(evse_template, evse)
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