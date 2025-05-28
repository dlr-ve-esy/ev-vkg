import marimo

__generated_with = "0.13.11"
app = marimo.App(width="medium", css_file="styles/custom.css")


@app.cell
def _(mo):
    mo.md(
        r"""
    # Knowledge Graph Analysis

    This is the best text
    """
    )
    return


@app.cell
def _():
    import marimo as mo
    from graph_expansions import expand_relational_csv, expand_bnezta
    from glob import glob
    from pathlib import Path
    from typing import List, Tuple
    from maplib import Mapping
    import polars as pl
    return (
        List,
        Mapping,
        Path,
        Tuple,
        expand_bnezta,
        expand_relational_csv,
        glob,
        mo,
    )


@app.cell
def _(mo):
    mo.md(r"""## Set global namespaces and load filepaths""")
    return


@app.cell
def _(List, Path, Tuple, glob, mo):
    CHIO = "https://dlr-ve-esy.github.io/charging-ontology/"
    VKG = "https://gitlab.dlr.de/vkg#"

    paths: List[Path] = [Path(f) for f in glob("operational/*")]
    mappings: List[Tuple[str, str]] = [(m.name, m.as_posix()) for m in paths]

    # load ottr templates for expansion
    with open("templates/evse.stottr", "r") as input_a:
        vkg_evse = input_a.read()
    with open("templates/common.stottr", "r") as input_b:
        vkg_common = input_b.read()
    mo.show_code()
    return VKG, mappings, vkg_common, vkg_evse


@app.cell
def _(mo):
    mo.md(r"""## Expand data into Knowledge Graph""")
    return


@app.cell
def _(
    Mapping,
    expand_bnezta,
    expand_relational_csv,
    mappings,
    mo,
    vkg_common,
    vkg_evse,
):
    m = Mapping([vkg_common, vkg_evse])
    for name, path in mappings:
        country: str = name.split("-")[0]
        if ("nobil" in name.lower()) or ("datexii" in path.lower()):
            expand_relational_csv("graph", path, m, challenge=False, country=country)
        if "bnetza" in name.lower():
            expand_bnezta("graph", path, m, challenge=False, country=country)
    mo.show_code()
    return (m,)


@app.cell
def _(mo):
    mo.md(r"""## Load Ontology into graph and perform reasoning""")
    return


@app.cell
def _(VKG, m, mo):
    TEST_GRAPH = f"{VKG}graph"
    m.read_triples("ontology/chio-full.ttl", transient=False, graph=TEST_GRAPH)
    mo.show_code()
    return (TEST_GRAPH,)


@app.cell
def _(TEST_GRAPH, m, mo):
    with open("reasoning/rdfs_subclass.sparql", "r") as input_c:
        rdfs_subclass = input_c.read()

    m.insert(rdfs_subclass, target_graph=TEST_GRAPH, source_graph=TEST_GRAPH)
    mo.md(f"""```sparql
    {rdfs_subclass}
    ```""")
    return


@app.cell
def _(TEST_GRAPH, m, mo):
    with open("reasoning/inverse_object_properties.sparql", "r") as input_d:
        inverse_object_properties = input_d.read()
    m.insert(
        inverse_object_properties, target_graph=TEST_GRAPH, source_graph=TEST_GRAPH
    )
    mo.md(f"""### Reason inverse object properties

    ```sparql
    {inverse_object_properties}
    ```""")
    return


@app.cell
def _(mo):
    mo.md(r"""## Perform queries""")
    return


@app.cell
def _(mo):
    with open("queries/total_aggregated_power_per_country_lower.sparql", "r") as input_e:
        total_aggregated_power_per_country_lower = input_e.read()
    mo.md(f"""### Total power accounting minimum EVSE potential 

    ```sparql
    {total_aggregated_power_per_country_lower}
    ```""")
    return (total_aggregated_power_per_country_lower,)


@app.cell
def _(TEST_GRAPH, m, total_aggregated_power_per_country_lower):
    m.query(total_aggregated_power_per_country_lower, graph=TEST_GRAPH)
    return


@app.cell
def _(mo):
    with open("queries/total_aggregated_power_per_country_upper.sparql", "r") as input_f:
        total_aggregated_power_per_country_upper = input_f.read()
    mo.md(f"""### Total power accounting maximum EVSE potential 

    ```sparql
    {total_aggregated_power_per_country_upper}
    ```""")
    return (total_aggregated_power_per_country_upper,)


@app.cell
def _(TEST_GRAPH, m, total_aggregated_power_per_country_upper):
    m.query(total_aggregated_power_per_country_upper, graph=TEST_GRAPH)
    return


if __name__ == "__main__":
    app.run()
