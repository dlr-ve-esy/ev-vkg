import marimo

__generated_with = "0.14.9"
app = marimo.App(
    width="medium",
    layout_file="layouts/main.slides.json",
    css_file="styles/custom.css",
)


@app.cell
def _():
    import json
    from widgets.cartogram import SourcesCartogramWidget, FAIRCartogramWidget
    from widgets.barchart import BarChartWidget, StackedBarChartWidget
    import marimo as mo
    from graph_expansions import expand_relational_csv, expand_bnezta
    from glob import glob
    from pathlib import Path
    from typing import List, Tuple
    from maplib import Mapping
    import polars as pl
    import requests
    from datetime import datetime
    import pyqrcode

    return (
        BarChartWidget,
        FAIRCartogramWidget,
        List,
        Mapping,
        Path,
        SourcesCartogramWidget,
        StackedBarChartWidget,
        Tuple,
        datetime,
        expand_bnezta,
        expand_relational_csv,
        glob,
        json,
        mo,
        pl,
        pyqrcode,
        requests,
    )


@app.cell
def _(mo):
    mo.md(
        r"""
    # Background
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
            width=int(539 * 1.3),
            height=int(404 * 1.3),
            marker_size=int(18 * 1.3),
            marker_size_secondary=7,
            legend_marker_size=13,
            legend_height=26,
        )
    )
    mo.md(f"""## The EAFO data ecosystem
    {widget}
    <p style="text-align: center;">Data providers disclosed as sources by the EAFO distribuited by state.</p>""")
    return


@app.cell
def _(BarChartWidget, mo, pl):
    country_codes = pl.read_csv("viz_data/code_mappings.csv")
    target_tracker = (
        pl.read_csv("viz_data/17.06.2025-eafo-target-tracker.csv")
        .join(country_codes, left_on="Category", right_on="Country", how="left")
        .select("Category", "Code", "Target kW", "Total power (kW) output")
        .with_columns(
            pl.col("Target kW").floordiv(1000).alias("target_mw"),
            pl.col("Total power (kW) output").floordiv(1000).alias("total_mw"),
        )
    )

    def df_to_dict(df: pl.DataFrame, key_col: str, value_col: str):
        """
        Get a Python dict from two columns of a DataFrame
        If the key column is not unique, the last row is used
        """
        return dict(df.select(key_col, value_col).iter_rows())

    capacities_plot = BarChartWidget(
        input=df_to_dict(target_tracker, key_col="Code", value_col="total_mw"),
        markers=df_to_dict(target_tracker, key_col="Code", value_col="target_mw"),
        bar_radius=4,
        bar_color="#de8f05",
        marker_color="#353839 ",
        width=539 * 2,
        height=202,
        y_ticks=[2000, 4000, 6000, 8000],
        y_label="Power (MW)",
        offset=36,
        font_size=1.1
    )
    cap_wg = mo.ui.anywidget(capacities_plot)
    cap_table = mo.ui.table(
        data=target_tracker.select("Code", "Target kW", "Total power (kW) output"),
        show_column_summaries=False,
        show_download=False,
    )
    mo.md(
        f"""
    # EAFO Policy performance reports

    Can the performance indicator reports provided by the EAFO be reproduced with the data published openly in context of the AFIR?

    {cap_wg}
    <p style="text-align: center;">According to the EAFOs criteria, all EU27 states reached the charging capacity targets.</p>
    {cap_table}
    """
    )
    return country_codes, df_to_dict, target_tracker


@app.cell
def _(mo, pl, sources_nap):
    considered_sources = sources_nap.with_columns(
        pl.col("id").str.split("-").list[0].alias("country")
    )

    sources_table = mo.ui.table(
        data=considered_sources.select(
            "country", "name", "publication_date", "metadata_url", "standard"
        ),
        show_column_summaries=False,
        show_download=False,
    )
    num_countries = len(considered_sources)
    avail_data = len(sources_nap.filter(~pl.col("local").is_null()))
    mo.md(
        f"""
    # FAIR Analysis

    As a proof of concept of our analysis we selected data reports published in the NAP of {num_countries} countries. From which only {avail_data} could be aqcuired, the rest is either behind a paywall or no longer availaible.
    {sources_table}
    """
    )
    return


@app.cell
def _(mo):
    INDENT = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"

    def colored_square(color):
        return f'<span style="display: inline-block; width: 10px; height: 10px; background-color: {color}; border-radius: 2px;"></span>'

    mo.md("""## Heuristics 

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
            latest_record["access_url"] is not None
        ):
            if latest_record["medium"] in optimal_access_media:
                fair_scores[ct]["F"] = 1
        elif latest_record["metadata_url"] is not None:
            fair_scores[ct]["F"] = 2
            if latest_record["actionable"]:
                fair_scores[ct]["F"] = 3
        # ACCESIBILITY
        if latest_record["access"] in accesible:
            fair_scores[ct]["A"] += 1
            if latest_record["metadata_url"] is not None:
                fair_scores[ct]["A"] += 1
                if latest_record["medium"] in optimal_access_media:
                    fair_scores[ct]["A"] += 1
        # INTEROPERABILITY
        if latest_record["standard"] == "DOCUMENTED":
            fair_scores[ct]["I"] += 1
        if latest_record["standard"] in interoperable_formats:
            fair_scores[ct]["I"] += 3
        # REUSABILITY
        if latest_record["license"] is not None:
            fair_scores[ct]["R"] += 1
            if latest_record["provenance"] == "TEXTUAL":
                fair_scores[ct]["R"] += 1
            elif latest_record["provenance"] == "EU":
                fair_scores[ct]["R"] += 2
        fair_scores[ct]["TOTAL"] = sum(list(fair_scores[ct].values()))

    totals = {k: s["TOTAL"] for k, s in fair_scores.items()}

    total_data = {
        k: v
        for k, v in sorted(totals.items(), key=lambda item: item[1], reverse=True)
        if v > 0
    }

    total_widget = BarChartWidget(
        input=total_data,
        bar_radius=4,
        bar_color="#9d6b92",
        width=539 * 2,
        height=202 * 2,
        y_max=12,
        y_ticks=[3, 6, 9],
        y_label="Score",
        offset=36,
    )
    wg = mo.ui.anywidget(total_widget)

    mo.md(f"""## Total FAIR Scores assigned by our methodology
    {wg}
    <p style="text-align: center;">States with zero score were excluded.</p>""")
    return fair_scores, sources_nap


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
def _(List, Path, Tuple, glob, mo):
    __CHIO = "https://dlr-ve-esy.github.io/charging-ontology/"
    VKG = "https://gitlab.dlr.de/vkg#"

    paths: List[Path] = [Path(f) for f in glob("operational/*")]
    mappings: List[Tuple[str, str]] = [(m.name, m.as_posix()) for m in paths]

    # load ottr templates for expansion
    with open("templates/evse.stottr", "r") as input_a:
        vkg_evse = input_a.read()
    with open("templates/common.stottr", "r") as input_b:
        vkg_common = input_b.read()

    snippet = "\n".join(vkg_evse.split("\n")[13:22])
    mo.md(f"""## Graph is expanded using OTTR templates

    The original sources are converted to a common tabular model which is expanded to a graph. For example, with this template we expand the data from a EVSE.
    ```
    {snippet}
    ```
    Each comand expands to different patterns.
    """)
    return VKG, mappings, vkg_common, vkg_evse


@app.cell
def _(
    Mapping,
    expand_bnezta,
    expand_relational_csv,
    mappings: "List[Tuple[str, str]]",
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


            if country == "NO":
                country_filter = ["NO", "SE", "IS"] 
            if country == "AT":
                country_filter = ["AT"] 
            else:
                country_filter = []    
            expand_relational_csv("graph", path, m, challenge=False, country=country, country_filter=country_filter)
        if "bnetza" in name.lower():
            expand_bnezta("graph", path, m, challenge=False, country=country)
    return (m,)


@app.cell
def _(Path, VKG, m, mo, pyqrcode, requests):
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

    qr = pyqrcode.create("https://dlr-ve-esy.github.io/charging-ontology/")
    Path("public").mkdir(exist_ok=True)
    img = "public/qr-code.png"
    qr.png(img, scale=5)

    m.read_triples("ontology/chio-full.ttl", transient=False, graph=TEST_GRAPH)
    mo.md("""## Load Ontology into graph and perform reasoning

    The charging ontology is in GitHub and it is hosted as a static site
    <p style="justify-content: space-evenly; display: flex;"><a href="https://github.com/dlr-ve-esy/charging-ontology" rel="noopener" target="_blank"><img alt="dlr-ve-esy/charging-ontology - GitHub" src="https://gh-card.dev/repos/dlr-ve-esy/charging-ontology.svg"></a><img src="public/qr-code.png" width="100"/></p>""")
    return (TEST_GRAPH,)


@app.cell
def _(mo):
    mo.md(
        """
    ## Visual summary of ontological commitments

    <p style="justify-content: space-evenly; display: flex;"><img src="public/mereology-summary.png"/></p>
    """
    )
    return


@app.cell
def _(TEST_GRAPH, m, mo):
    with open("reasoning/charging_connector.sparql", "r") as input_c:
        charging_connector = input_c.read()

    m.insert(charging_connector, target_graph=TEST_GRAPH, source_graph=TEST_GRAPH)
    mo.md(f"""## Perform reasoning

    In theory, we could try to infer all the axioms of the graph, but doing so would consume a lot of memory. We only need a handful of inferences so we perform them individually.

    ### Infer connector class

    We find everything that is being assigned to a subclass of connector and  assign it the connector class
    ```sparql
    {charging_connector}
    ```""")
    return


@app.cell
def _(TEST_GRAPH, m, mo):
    with open("reasoning/has_part.sparql", "r") as input_d:
        has_part = input_d.read()
    m.insert(has_part, target_graph=TEST_GRAPH, source_graph=TEST_GRAPH)
    mo.md(f"""### Mereology: "has part" is inverse of "part of"

    When an object A is part of some object B means that that B has A as part. 

    Common logic axiomatization:
    ```lisp
    (cl:comment "continuant-part-of and has-continuant-part are inverse relations [eld-1]"
      (forall (t a b)
        (iff (continuant-part-of a b t) (has-continuant-part b a t))))
    ```

    SPARQL query:
    ```sparql
    {has_part}
    ```""")
    return


@app.cell
def _(TEST_GRAPH, m, mo):
    with open("reasoning/part_of.sparql", "r") as input_g:
        part_of = input_g.read()
    m.insert(part_of, target_graph=TEST_GRAPH, source_graph=TEST_GRAPH)
    mo.md(f"""### Mereology: "part of" is transitive

    If A is part of B and B is part of C then A is part of C.

    Common logic axiomatization:
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
    ```
    Note that the inverse relation, "has part" is not transitive
    """)
    return


@app.cell
def _(mo):
    mo.md(
        """
    ### Mereology: "part of" is reflexive

    Everything is a part of itself, in BFO "part of" is a primitive relation and has axioms to distinguish it from "proper part of" where reflixibility is excluded.

    Common logic axiomatization:
    ```lisp
    (cl:comment "continuant-part-of is reflexive at a time [mcd-1]"
      (forall (a t)
        (if (instance-of a independent-continuant t)
          (continuant-part-of a a t))))
    ```

    In this excercise we have no practical application for this property, so we do not infer it.
    """
    )
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
def _(
    TEST_GRAPH,
    df_to_dict,
    m,
    pl,
    target_tracker,
    total_aggregated_power_per_country_lower,
):
    aggregated_power_df = m.query(
        total_aggregated_power_per_country_lower, graph=TEST_GRAPH
    )
    study_filter = list(aggregated_power_df["code"].unique())
    results = (
        target_tracker.join(
            aggregated_power_df, left_on="Code", right_on="code", how="left"
        )
        .with_columns(pl.col("total_accounted_power").fill_null(0).truediv(1000))
        .filter(pl.col("Code").is_in(study_filter))
    )

    result_codes = list(aggregated_power_df["code"].unique())
    filtered_markers = {
        k: v
        for k, v in df_to_dict(results, key_col="Code", value_col="target_mw").items()
        if k in result_codes
    }
    return filtered_markers, results, study_filter


@app.cell
def _(BarChartWidget, df_to_dict, filtered_markers, results):
    results_plot = BarChartWidget(
        input=df_to_dict(results, key_col="Code", value_col="total_accounted_power"),
        shadow=df_to_dict(results, key_col="Code", value_col="total_mw"),
        markers=filtered_markers,
        bar_radius=4,
        bar_color="#0173b2",
        marker_color="#353839",
        shadow_color="#d55e00",
        width=539 * 2,
        height=202 * 2,
        y_max=10000,
        y_ticks=[2000, 4000, 6000, 8000],
        y_label="Power (MW)",
        offset=60,
        font_size = 1.18
    )

    results_plot
    return


@app.cell
def _(mo):
    with open("queries/total_evses_per_power.sparql", "r") as input_f:
        total_evses_per_power = input_f.read()
    mo.md(f"""### Count of EVSES based on max nominal capacity

    ```sparql
    {total_evses_per_power}
    ```""")
    return (total_evses_per_power,)


@app.cell
def _(TEST_GRAPH, m, pl, study_filter, total_evses_per_power):
    total_evses_per_power_df = m.query(total_evses_per_power, graph=TEST_GRAPH)
    total_evses_per_power_df = total_evses_per_power_df.pivot("power_bin", index="code", values="evse_count").select(
            [
                "code",
                "0-7,4 kW",
                "7,4-22 kW",
                "22-50 kW",
                "50-150 kW",
                "150-350 kW",
                "350+ kW",
            ]
        ).filter(pl.col("code").is_in(study_filter)).sort(by="code")
    total_evses_per_power_df
    return (total_evses_per_power_df,)


@app.cell
def _(StackedBarChartWidget, total_evses_per_power_df):
    cat_colors = {
        "0-7,4 kW": "#9dc291",
        "7,4-22 kW": "#73a861",
        "22-50 kW": "#527a44",
        "50-150 kW": "#e9cf6f",
        "150-350 kW": "#e0ba2f",
        "350+ kW": "#aa8b1a",
    }

    chart_input = total_evses_per_power_df.to_dicts()

    stacked_chart = StackedBarChartWidget(
        input=chart_input,
        x_key="code",
        bar_radius=4,
        cat_colors=cat_colors,
        width=539 * 2,
        height=202 * 2,
        y_label="counts",
        offset=36,
        legend = False
    )

    stacked_chart
    return (cat_colors,)


@app.cell
def _(country_codes, pl, study_filter):
    power_counts_tracker = (
        pl.read_csv("viz_data/17.06.2025-eafo-counts.csv")
        .join(country_codes, left_on="Category", right_on="Country", how="left")
        .with_columns(
            pl.col("Code").alias("code"),
            pl.col("Slow AC recharging point, single-phase (P < 7.4kW)").alias("0-7,4 kW"),
            pl.col("Medium-speed AC recharging point, triple-phase (7.4kW ≤ P ≤ 22kW)").alias("7,4-22 kW"),
            pl.sum_horizontal("Fast AC recharging point, triple-phase (P > 22kW)", "Slow DC recharging point (P < 50kW)").alias("22-50 kW"),
            pl.col("Fast DC recharging point (50kW ≤ P < 150kW)").alias("50-150 kW"),
            pl.col("Level 1 - Ultra-fast DC recharging point (150kW ≤ P < 350kW)").alias("150-350 kW"),
            pl.col("Level 2 - Ultra-fast DC recharging point (P ≥ 350kW)").alias("350+ kW"),

        ).select(
            [
                "code",
                "0-7,4 kW",
                "7,4-22 kW",
                "22-50 kW",
                "50-150 kW",
                "150-350 kW",
                "350+ kW",
            ]
        ).filter(pl.col("code").is_in(study_filter)).sort(by="code")
    )
    power_counts_tracker

    return (power_counts_tracker,)


@app.cell
def _(StackedBarChartWidget, cat_colors, power_counts_tracker):
    chart_input_2 = power_counts_tracker.to_dicts()

    stacked_chart_2 = StackedBarChartWidget(
        input=chart_input_2,
        x_key="code",
        bar_radius=4,
        cat_colors=cat_colors,
        width=539 * 2,
        height=202 * 2,
        y_label="counts",
        offset=31,
        legend = True
    )

    stacked_chart_2
    return


if __name__ == "__main__":
    app.run()
