import marimo

__generated_with = "0.13.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from from_relational_csv import expand_relational_csv
    from glob import glob
    from pathlib import Path
    from typing import List, Tuple
    from maplib import Mapping
    return List, Mapping, Path, Tuple, expand_relational_csv, glob


@app.cell
def _():
    CHIO = "https://dlr-ve-esy.github.io/charging-ontology/"
    VKG = "https://gitlab.dlr.de/vkg#"

    CHALLENGE_MODE = True
    return (VKG,)


@app.cell
def _(List, Mapping, Path, Tuple, VKG, expand_relational_csv, glob):
    paths: List[Path] = [Path(f) for f in glob("operational/*")]
    mappings: List[Tuple[str, str]] = [(m.name, m.as_posix()) for m in paths]

    with open("templates/evse.stottr", "r") as d:
        vkg_evse = d.read()
    with open("templates/common.stottr", "r") as d:
        vkg_common = d.read()
    m = Mapping([vkg_common, vkg_evse])

    for name, path in mappings:
        if ("nobil" in name.lower()) or ("datexii" in path.lower()):
            country: str = name.split("-")[0]
            expand_relational_csv("graph", path, m, challenge=False, country=country)

    TEST_GRAPH = f"{VKG}graph"
    m.read_triples("ontology/chio-full.ttl", transient=False, graph=TEST_GRAPH)

    with open("reasoning/rdfs_subclass.sparql", "r") as d:
        rdfs_subclass = d.read()

    with open("reasoning/inverse_object_properties.sparql", "r") as d:
        inverse_object_properties = d.read()

    with open("queries/total_aggregated_power_per_country.sparql", "r") as d:
        total_aggregated_power_per_country = d.read()

    m.insert(rdfs_subclass, target_graph=TEST_GRAPH, source_graph=TEST_GRAPH)
    m.insert(
        inverse_object_properties, target_graph=TEST_GRAPH, source_graph=TEST_GRAPH
    )

    print(m.query(total_aggregated_power_per_country, graph=TEST_GRAPH))
    return


if __name__ == "__main__":
    app.run()
