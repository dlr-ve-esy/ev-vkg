import marimo

__generated_with = "0.13.11"
app = marimo.App(width="medium", css_file="styles/custom.css")


@app.cell
def _():
    import json
    from widgets.cartogram import SourcesCartogramWidget, FAIRCartogramWidget
    from widgets.barchart import BarChartWidget
    import marimo as mo
    from graph_expansions import expand_relational_csv, expand_bnezta
    from glob import glob
    from pathlib import Path
    from typing import List, Tuple
    from maplib import Mapping
    import polars as pl
    import requests
    from datetime import datetime
    return (
        BarChartWidget,
        FAIRCartogramWidget,
        List,
        Mapping,
        Path,
        SourcesCartogramWidget,
        Tuple,
        datetime,
        expand_bnezta,
        expand_relational_csv,
        glob,
        json,
        mo,
        pl,
        requests,
    )


@app.cell
def _(mo):
    mo.md(r"""# Background""")
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Charging infrastructure data from the AFIR

    - The European union published in 2023 the Alternative Fuels Infrastructure Regulation (AFIR)
    - This regulation contains data provisions regarding the availability of charging infrastructure data.
    - The union reports the regulations performance through European Alternative Fuels Observatory (EAFO)
    - Some of the sources reported by the EAFO cannot be validated.
    """
    )
    return


@app.cell
def _(json):
    with open("viz_data/sources_per_country.json", "r") as f:
        sources_per_country = json.load(f)
    with open("viz_data/source_colors.json", "r") as f:
        source_colors = json.load(f)
    with open("viz_data/color_legend.json", "r") as f:
        color_legend = json.load(f)
    with open("viz_data/countries_9x9_xy.json", "r") as f:
        country_grid = json.load(f)
    with open("viz_data/spectrum_colors.json", "r") as f:
        spectrum_colors = json.load(f)
    return (
        color_legend,
        country_grid,
        source_colors,
        sources_per_country,
        spectrum_colors,
    )


@app.cell
def _(
    SourcesCartogramWidget,
    color_legend,
    country_grid,
    mo,
    source_colors,
    sources_per_country,
):
    widget = mo.ui.anywidget(
        SourcesCartogramWidget(
            sources_per_country=sources_per_country,
            source_colors=source_colors,
            color_legend=color_legend,
            country_grid=country_grid,
        )
    )
    mo.md(f"""## The EAFO data ecosystem
    {widget}
    <p style="text-align: center;">Data providers disclosed as sources by the EAFO distribuited by state.</p>""")
    return


@app.cell
def _(mo):
    INDENT = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"

    def colored_square(color):
        return f'<span style="display: inline-block; width: 10px; height: 10px; background-color: {color}; border-radius: 2px;"></span>'

    mo.md(f"""# FAIR Analysis

    ## Heuristics 

    To address the FAIR alignment of the charging infrastructure data provided by EU+ states we rely on a simple set of heuristics.  
    The final values of the assesment are summed to calculate the final score""")
    return INDENT, colored_square


@app.cell
def _(INDENT, colored_square, mo):
    mo.md(
        f"""
    ### Findability

    {INDENT}{colored_square("#c2cfdf")} If the resource can be accessed through a URL but has no metadata associated, we assign it one point.  
    {INDENT}{colored_square("#6181ab")} If the resource has a persistent metadata descriptor we assign it two points.  
    {INDENT}{colored_square("#435d7f")} If said metadata record is in a standarized actionable format (DCAT, OEMetadata) we assign it three points. 

    ### Accesibility

    {INDENT}{colored_square("#e9cf6f")} If the metadata reports clear paths of accesibility we add a point to the score.  
    {INDENT}{colored_square("#e0ba2f")} If the repository allows persisting archived versions of the data we assign a point.  
    {INDENT}{colored_square("#aa8b1a")} If the access media is either an API or an archive we assign a point.
    """
    )
    return


@app.cell
def _(INDENT, colored_square, mo):
    mo.md(
        f"""
    ### Interoperability

    {INDENT}{colored_square("#d97c78")} If the resource has a non-standarized exchange format but has rich documentation it gets one point.  
    {INDENT}{colored_square("#c8433e")} If the resource follows an standard format but such format can't be validated with an automatic tool it gets two points.  
    {INDENT}{colored_square("#932d2a")} If the standard format can be validated with automatic tools it gets three points. 

    ### Reusability

    {INDENT}{colored_square("#9dc291")} If the resource provides a clear license it gets one point.  
    {INDENT}{colored_square("#73a861")} If the resource records provenance textually it gets a point.  
    {INDENT}{colored_square("#527a44")} If the resource properly uses  the EU framework as source it gets an additional point.
    """
    )
    return


@app.cell
def _(BarChartWidget, datetime, mo, pl, sources_per_country):
    sources_nap = pl.read_csv("sources/metadata.csv")
    sources_nap = sources_nap.with_columns(
        pl.col("actionable").replace_strict({"NO": False, "YES": True}),
        pl.col("identifier").replace_strict({"NO": False, "YES": True}),
    )

    countries = list(sources_per_country.keys())

    fair_scores = {c: {"F": 0, "A": 0, "I": 0, "R": 0, "TOTAL": 0} for c in countries}
    accesible = [
        "OPEN",
        "REGISTERED_USERS",
        "PER_REQUEST",
    ]
    optimal_access_media = ["ARCHIVE", "API"]
    interoperable_formats = ["OCPI", "OICP", "DATEXII"]
    for ct in countries:
        records = sources_nap.filter(
            pl.col("id").str.slice(0, 2).str.contains(ct)
        ).to_dicts()
        if len(records) == 0:
            continue
        dates = [datetime.strptime(r["publication_date"], "%m/%d/%Y") for r in records]
        latest_idx = dates.index(max(dates))
        latest_record = records[latest_idx]
        # FINDABILITY
        if (latest_record["metadata_url"] is None) & (
            not (latest_record["access_url"] is None)
        ):
            if latest_record["medium"] in optimal_access_media:
                fair_scores[ct]["F"] = 1
        elif not (latest_record["metadata_url"] is None):
            fair_scores[ct]["F"] = 2
            if latest_record["actionable"]:
                fair_scores[ct]["F"] = 3
        # ACCESIBILITY
        if latest_record["access"] in accesible:
            fair_scores[ct]["A"] += 1
            if not (latest_record["metadata_url"] is None):
                fair_scores[ct]["A"] += 1
                if latest_record["medium"] in optimal_access_media:
                    fair_scores[ct]["A"] += 1
        # INTEROPERABILITY
        if latest_record["standard"] == "DOCUMENTED":
            fair_scores[ct]["I"] += 1
        if latest_record["standard"] in interoperable_formats:
            fair_scores[ct]["I"] += 3
        # REUSABILITY
        if not (latest_record["license"] is None):
            fair_scores[ct]["R"] += 1
            if latest_record["provenance"] == "TEXTUAL":
                fair_scores[ct]["R"] += 1
            elif latest_record["provenance"] == "EU":
                fair_scores[ct]["R"] += 2
        fair_scores[ct]["TOTAL"] = sum(list(fair_scores[ct].values()))

    totals = {k: s["TOTAL"] for k, s in fair_scores.items()}

    total_data ={k: v for k, v in sorted(totals.items(), key=lambda item: item[1], reverse=True) if v > 0}
    wg = mo.ui.anywidget(BarChartWidget(
            input=total_data,
            bar_radius=4,
            bar_color="#9d6b92",
            width=539,
            height=404,
            y_max= 12,
            y_ticks = [3,6,9]
        ))



    mo.md(f"""## Total FAIR Scores assigned by our methodology
    {wg}
    <p style="text-align: center;">States with zero score were excluded.</p>""")
    return (fair_scores,)


@app.cell
def _(FAIRCartogramWidget, country_grid, fair_scores, mo, spectrum_colors):
    fair_widget = mo.ui.anywidget(
        FAIRCartogramWidget(
            fair_scores=fair_scores,
            source_colors=spectrum_colors,
            country_grid=country_grid,
        )
    )
    mo.md(f"""## FAIR Scores by principle
    {fair_widget}""")
    return


@app.cell
def _(mo):
    mo.md(r"""# Knowledge Graph Analysis""")
    return


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
        if (
            ("nobil" in name.lower())
            or ("datexii" in path.lower())
            or ("irve" in path.lower())
        ):
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
def _(Path, VKG, m, mo, requests):
    TEST_GRAPH = f"{VKG}graph"
    ONTOLOGY_IRI = (
        "https://dlr-ve-esy.github.io/charging-ontology/releases/0.2.0/chio-full.ttl"
    )
    ONTOLOGY_LOCAL = "ontology/chio-full.ttl"
    if not (p := Path(ONTOLOGY_LOCAL)).exists():
        response = requests.get(ONTOLOGY_IRI)
        if response.status_code == 200:
            with open(p, "wb") as onto_file:
                onto_file.write(response.content)


    m.read_triples("ontology/chio-full.ttl", transient=False, graph=TEST_GRAPH)
    mo.show_code()
    return (TEST_GRAPH,)


@app.cell
def _(TEST_GRAPH, m, mo):
    with open("reasoning/charging_connector.sparql", "r") as input_c:
        charging_connector = input_c.read()

    m.insert(charging_connector, target_graph=TEST_GRAPH, source_graph=TEST_GRAPH)
    mo.md(f"""### Infer connector class

    ```sparql
    {charging_connector}
    ```""")
    return


@app.cell
def _(TEST_GRAPH, m, mo):
    with open("reasoning/has_part.sparql", "r") as input_d:
        has_part = input_d.read()
    m.insert(has_part, target_graph=TEST_GRAPH, source_graph=TEST_GRAPH)
    mo.md(f"""### Mereology: has part

    ```sparql
    {has_part}
    ```""")
    return


@app.cell
def _(TEST_GRAPH, m, mo):
    with open("reasoning/part_of.sparql", "r") as input_g:
        part_of = input_g.read()
    m.insert(part_of, target_graph=TEST_GRAPH, source_graph=TEST_GRAPH)
    mo.md(f"""### Mereology: part of
    Common logic axiomatization from BFO:
    ```lisp
    (cl:comment "continuant-part-of is transitive at a time [plp-1]"
    (forall (a b c t t2)
     (if
      (and (continuant-part-of a b t) (continuant-part-of b c t2)
       (temporal-part-of t t2))
      (continuant-part-of a c t))))
    ```
    SPARQL query:
    ```sparql
    {part_of}
    ```""")
    return


@app.cell
def _(mo):
    mo.md(r"""## Perform queries""")
    return


@app.cell
def _(mo):
    with open(
        "queries/total_aggregated_power_per_country_lower.sparql", "r"
    ) as input_e:
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


if __name__ == "__main__":
    app.run()
