import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", css_file="styles/custom.css")


@app.cell
def _(mo):
    mo.md(r"""
    # FAIR Electric Vehicle Charging Infrastructure Data
    ## Enabling digital preservation of policy performance analyses
    ### Arellano Ruiz et al.
    """)
    return


@app.cell
def _():
    import json
    from widgets.cartogram import SourcesCartogramWidget, FAIRCartogramWidget
    from widgets.barchart import (
        BarChartWidget,
        DoubleStackedBarChartWidget,
        FAIRBarChartsWidget,
        FAIRDatasetScoresWidget,
        GroupedBarChartWidget,
    )
    from widgets.heatmap import HeatMapWidget
    from widgets.grid_scatter import GridScatterWidget
    from widgets.vkg_schematic import VkgSchematicWidget
    import marimo as mo
    from graph.graph_expansions import expand_relational_csv, expand_bnezta
    from glob import glob
    from pathlib import Path
    from typing import List, Tuple
    from maplib import Mapping
    import polars as pl
    import requests
    from datetime import datetime
    import pyqrcode
    from great_tables import GT
    import error_metrics as em
    import fair_scoring as fs
    import run_config as rc

    data_folder = "parsed"
    return (
        BarChartWidget,
        DoubleStackedBarChartWidget,
        FAIRBarChartsWidget,
        FAIRCartogramWidget,
        FAIRDatasetScoresWidget,
        GT,
        GridScatterWidget,
        GroupedBarChartWidget,
        HeatMapWidget,
        List,
        Mapping,
        Path,
        SourcesCartogramWidget,
        Tuple,
        VkgSchematicWidget,
        data_folder,
        em,
        expand_bnezta,
        expand_relational_csv,
        fs,
        glob,
        json,
        mo,
        pl,
        pyqrcode,
        rc,
        requests,
    )


@app.cell
def _(rc):
    # The run configuration is the persisted source selection: dataset
    # IDs, snapshot dates, input paths, checksums, analysis inclusion,
    # country coverage and exclusion reasons (run_config.yaml). The
    # analysis no longer relies on notebook checkbox state.
    config = rc.load()
    checksum_problems = rc.verify_checksums(config)
    config
    return (config,)


@app.cell
def _(mo):
    mo.md(r"""
    # Background
    ## Charging infrastructure data from the AFIR

    - The European union published in 2023 the Alternative Fuels Infrastructure Regulation (AFIR)
    - This regulation contains data provisions regarding the availability of charging infrastructure data.
    - The union reports the regulations performance through European Alternative Fuels Observatory (EAFO)
    - Some of the sources reported by the EAFO cannot be validated.
    """)
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
    mo.md(
        f"""## The EAFO data ecosystem
    {widget}
    <p style="text-align: center;">Data providers disclosed as sources by the EAFO distribuited by state.</p>"""
    )
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

    capacities_plot_a = BarChartWidget(
        input=df_to_dict(
            target_tracker.filter(pl.col("total_mw") > 400),
            key_col="Code",
            value_col="total_mw",
        ),
        markers=df_to_dict(
            target_tracker.filter(pl.col("total_mw") > 400),
            key_col="Code",
            value_col="target_mw",
        ),
        bar_radius=4,
        bar_color="#de8f05",
        marker_color="#353839 ",
        width=397 * 2,  # 539 for paper
        height=101,  # 101 for paper
        y_ticks=[2000, 4000, 6000, 8000],
        y_grid=[2000, 4000, 6000, 8000],
        y_label="Power (MW)",
        y_max=8000,
        offset=36,
        font_size=0.9,
        margin={"top": 14, "right": 10, "bottom": 20, "left": 34},  # right 0 for paper
    )

    capacities_plot_b = BarChartWidget(
        input=df_to_dict(
            target_tracker.filter(pl.col("total_mw") <= 400),
            key_col="Code",
            value_col="total_mw",
        ),
        markers=df_to_dict(
            target_tracker.filter(pl.col("total_mw") <= 400),
            key_col="Code",
            value_col="target_mw",
        ),
        bar_radius=4,
        bar_color="#de8f05",
        marker_color="#353839 ",
        width=397 * 2,  # 539 for paper
        height=101,  # 101 for paper
        y_ticks=[100, 200, 300, 400],
        y_grid=[100, 200, 300, 400],
        y_label="",
        y_max=400,
        offset=36,
        font_size=0.9,
        margin={"top": 8, "right": 10, "bottom": 18, "left": 34},
    )
    cap_wg_a = mo.ui.anywidget(capacities_plot_a)
    cap_wg_b = mo.ui.anywidget(capacities_plot_b)
    cap_table = mo.ui.table(
        data=target_tracker.select("Code", "Target kW", "Total power (kW) output"),
        show_column_summaries=False,
        show_download=False,
    )
    mo.md(
        f"""
    # EAFO Policy performance reports

    Can the performance indicator reports provided by the EAFO be reproduced with the data published openly in context of the AFIR?

    {cap_wg_a}
    {cap_wg_b}
    <p style="text-align: center;">According to the EAFOs criteria, all EU27 states reached the charging capacity targets.</p>
    {cap_table}
    """
    )
    return country_codes, df_to_dict, target_tracker


@app.cell
def _(fs, mo, pl, sources_nap):
    # One row per assessed dataset (the latest assessment record,
    # selected by parsed publication date): 23 datasets from 22
    # countries, with both German datasets (de.1, de.2) visible.
    considered_sources = fs.latest_record_per_dataset(sources_nap).with_columns(
        pl.col("dataset_id").str.split(".").list[0].str.to_uppercase().alias("country")
    )

    sources_table = mo.ui.table(
        data=considered_sources.select(
            "dataset_id",
            "country",
            "name",
            "publication_date",
            "metadata_url",
            "standard",
        ),
        show_column_summaries=False,
        show_download=False,
    )
    num_datasets = considered_sources.height
    num_countries = considered_sources["country"].n_unique()
    avail_data = considered_sources.filter(~pl.col("local").is_null()).height
    mo.md(
        f"""
    # FAIR Analysis

    As a proof of concept of our analysis we selected data reports published in the NAPs of {num_countries} countries, comprising {num_datasets} assessed datasets. From which only {avail_data} could be acquired, the rest is either behind a paywall or no longer available.
    {sources_table}
    """
    )
    return (considered_sources,)


@app.cell
def _(mo):
    INDENT = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"

    def colored_square(color):
        return f'<span style="display: inline-block; width: 10px; height: 10px; background-color: {color}; border-radius: 2px;"></span>'

    mo.md(
        """## Heuristics 

    To address the FAIR alignment of the charging infrastructure data provided by EU+ states we rely on a simple set of heuristics.  
    The final values of the assesment are summed to calculate the final score"""
    )
    return INDENT, colored_square


@app.cell
def _(INDENT, colored_square, mo):
    mo.md(f"""
    ### Findability

    {INDENT}{colored_square("#c2cfdf")} If the resource can be accessed through a URL but has no metadata associated, we assign it one point.  
    {INDENT}{colored_square("#6181ab")} If the resource has a persistent metadata descriptor we assign it two points.  
    {INDENT}{colored_square("#435d7f")} If said metadata record is in a standarized actionable format (DCAT, OEMetadata) we assign it three points. 

    ### Accesibility

    {INDENT}{colored_square("#e9cf6f")} If the metadata reports clear paths of accesibility we add a point to the score.  
    {INDENT}{colored_square("#e0ba2f")} If the access endpoint is shared we assign one point.  
    {INDENT}{colored_square("#aa8b1a")} If the access media is either an API or an archive we assign a point.
    """)
    return


@app.cell
def _(INDENT, colored_square, mo):
    mo.md(f"""
    ### Interoperability

    {INDENT}{colored_square("#d97c78")} If the resource has a non-standarized exchange format but has rich documentation it gets one point.  
    {INDENT}{colored_square("#c8433e")} If the resource follows an standard format but such format can't be validated with an automatic tool it gets two points.  
    {INDENT}{colored_square("#932d2a")} If the standard format can be validated with automatic tools it gets three points. 

    ### Reusability

    {INDENT}{colored_square("#9dc291")} If the resource provides a clear license it gets one point.  
    {INDENT}{colored_square("#73a861")} If the resource records provenance textually it gets a point.  
    {INDENT}{colored_square("#527a44")} If the resource properly uses  the EU framework as source it gets an additional point.
    """)
    return


@app.cell
def _(BarChartWidget, config, fs, mo, sources_per_country):
    # Metadata with booleans and dates parsed; dataset identity comes
    # from the stable dataset_id column, never from date-containing
    # record IDs or substring matching.
    sources_nap = fs.load_sources("sources/metadata.csv")

    countries = list(sources_per_country.keys())

    # One FAIR score row per assessed dataset (23 rows, both German
    # datasets separate), scored from the latest assessment record of
    # each dataset by fair_scoring.score_record.
    scores_df = fs.dataset_scores(sources_nap)

    # Country-level view for the cartogram and the total chart. The
    # selection rule is explicit and deterministic (fair_scoring.
    # country_view): a country with several assessed datasets is
    # represented by the dataset included in the quantitative
    # comparison (de.2 for Germany); a country with a single assessed
    # dataset is represented by that dataset.
    analysis_dataset_ids = [d.dataset_id for d in config.analysis_datasets()]
    selected_country_scores = fs.country_view(scores_df, analysis_dataset_ids)

    fair_scores_country = {
        c: {"F": 0, "A": 0, "I": 0, "R": 0, "TOTAL": 0} for c in countries
    }
    for c, scores in selected_country_scores.items():
        if c in fair_scores_country:
            fair_scores_country[c] = scores

    totals = {
        c: scores["TOTAL"]
        for c, scores in fair_scores_country.items()
    }
    total_data = {
        k: v
        for k, v in sorted(totals.items(), key=lambda item: item[1], reverse=True)
        if v > 0
    }

    total_widget = BarChartWidget(
        input=total_data,
        bar_radius=4,
        bar_color="#9d6b92",
        width=397 * 2,  # 549 for paper figure
        height=101 * 2,
        y_max=12,
        y_ticks=[3, 6, 9, 12],
        y_grid=[3, 6, 9, 12],
        y_label="Total Score",
        font_size=1.2,
        offset=36,
        margin={"top": 17, "right": 0, "bottom": 20, "left": 22},  # For paper use top 6
    )
    wg = mo.ui.anywidget(total_widget)

    mo.md(
        f"""## Total FAIR Scores assigned by our methodology
    {wg}
    <p style="text-align: center;">States with zero score were excluded.</p>"""
    )
    return fair_scores_country, scores_df, sources_nap, total_data


@app.cell
def _(sources_nap):
    sources_nap
    return


@app.cell
def _(
    FAIRCartogramWidget,
    country_grid,
    fair_scores_country,
    mo,
    spectrum_colors,
):
    fair_widget = mo.ui.anywidget(
        FAIRCartogramWidget(
            fair_scores=fair_scores_country,
            source_colors=spectrum_colors,
            country_grid=country_grid,
        )
    )
    mo.md(
        f"""## FAIR Scores by principle
    {fair_widget}"""
    )
    return


@app.cell
def _(scores_df):
    f_scores = {}
    f_scores_datasets = []
    for _k, _v in scores_df.partition_by("dataset_id", include_key=True, as_dict=True).items():
        _rs = _v.row(named=True)
        f_scores[_k[0]] = _rs
        _rs["code "] = _rs["dataset_id"]
        f_scores_datasets.append(_rs)
    f_scores
    return f_scores, f_scores_datasets


@app.cell
def _(fair_scores_dataset):
    fair_scores_dataset
    return


@app.cell
def _(FAIRBarChartsWidget, f_scores, json, mo, spectrum_colors):
    # Dataset-level FAIR scores (Table 8 unit) in the principle grid,
    # so the two German datasets are both visible.
    with open("viz_data/fair_scores_datasets.json", "r", encoding="utf-8") as _fd:
        fair_scores_dataset = {row["code"]: row for row in json.load(_fd)}
    fair_bars_widget = mo.ui.anywidget(
        FAIRBarChartsWidget(
            fair_scores=f_scores,
            source_colors=spectrum_colors,
        )
    )
    mo.md(
        f"""## FAIR dataset scores by principle and total
    {fair_bars_widget}"""
    )
    return (fair_scores_dataset,)


@app.cell
def _(FAIRDatasetScoresWidget, f_scores_datasets, json, mo):
    # Dataset-level FAIR scores (Table 8 unit): one stacked bar per
    # dataset, so the two German datasets are both visible.
    with open("viz_data/fair_scores_datasets.json", "r", encoding="utf-8") as _f:
        fair_scores_datasets = json.load(_f)
    fair_dataset_widget = mo.ui.anywidget(
        FAIRDatasetScoresWidget(input=f_scores_datasets)
    )
    mo.md(
        f"""## FAIR Scores per dataset
    {fair_dataset_widget}"""
    )
    return (fair_scores_datasets,)


@app.cell
def _(fair_scores_datasets):
    fair_scores_datasets
    return


@app.cell
def _(f_scores):
    list(f_scores.values())
    return


@app.cell
def _(considered_sources, pl):
    metadata_name_map = {
        "own-standard": "Own standard",
        "mobility-dcat-ap": "Mobility DCAT-AP",
    }
    access_map = {
        "OPEN": "Open access",
        "REGISTERED_USERS": "Registration needed",
        "PER_REQUEST": "Per request",
        "CLOSED": "Closed",
        "UNAVAILABLE": "Unavailable",
        "NONDOCUMENTED": "Unavailable",
    }

    standard_map = {
        "DATEXII": "DATEX II",
        "DATEXII_P": "DATEX II modified",
        "OCPI": "OCPI",
        "OICP": "OICP",
        "DOCUMENTED": "Documented",
        "UNDOCUMENTED": "Not documented",
    }

    medium_map = {
        "API": "API",
        "DUMP": "Download",
        "DASHBOARD": "Dashboard",
        "ARCHIVE": "Archive",
    }

    provenance_map = {
        "EU": "AFIR",
        "NONE": "Not documented",
        "LSV": "German Charging station regulation (LSV)",
        "TEXTUAL": "Textually documented",
    }
    latex_output = considered_sources.select(
        pl.col("country").alias("Country"),
        pl.col("source").alias("Source"),
        pl.col("provider").alias("Provider"),
        pl.col("publication_date")
        .dt.to_string("%d %b, %Y")
        .alias("Publication Date"),
        pl.when(pl.col("metadata_url").is_null())
        .then(pl.lit("No"))
        .otherwise(pl.lit("Yes"))
        .alias("Metadata"),
        pl.when(pl.col("access_url").is_null())
        .then(pl.lit("No"))
        .otherwise(pl.lit("Yes"))
        .alias("Endpoint"),
        pl.when(pl.col("metadata_standard").is_null())
        .then(pl.lit("No standard"))
        .otherwise(pl.col("metadata_standard").replace(metadata_name_map))
        .alias("Metadata standard"),
        pl.when(pl.col("actionable"))
        .then(pl.lit("Yes"))
        .otherwise(pl.lit("No"))
        .alias("Actionable"),
        pl.when(pl.col("access").is_null())
        .then(pl.lit("Unavailable"))
        .otherwise(pl.col("access").replace(access_map))
        .alias("Access"),
        pl.when(pl.col("medium").is_null())
        .then(pl.lit("Unavailable"))
        .otherwise(pl.col("medium").replace(medium_map))
        .alias("Media"),
        pl.when(pl.col("standard").is_null())
        .then(pl.lit("Not documented"))
        .otherwise(pl.col("standard").replace(standard_map))
        .alias("Data model"),
        pl.when(pl.col("provenance").is_null())
        .then(pl.lit("Not documented"))
        .otherwise(pl.col("provenance").replace(provenance_map))
        .alias("Provenance"),
        pl.when(pl.col("license").is_null())
        .then(pl.lit("Not documented"))
        .when(pl.col("license").str.contains("http"))
        .then(pl.lit("Custom"))
        .otherwise(pl.col("license").replace(standard_map))
        .alias("License"),
    )

    # Stable dataset IDs (at.1, de.1, de.2, ...) instead of
    # order-dependent per-country counters.
    latex_output = latex_output.with_columns(
        pl.col("dataset_id").alias("Identifier")
    )

    general_information = latex_output.select(
        pl.col("Identifier"),
        pl.col("Country"),
        pl.col("Source"),
        pl.col("Provider"),
        pl.col("Publication Date"),
    )

    findability_criteria = latex_output.select(
        pl.col("Identifier"),
        pl.col("Metadata"),
        pl.col("Actionable"),
        pl.col("Metadata standard"),
    )

    accessibility_criteria = latex_output.select(
        pl.col("Identifier"), pl.col("Access"), pl.col("Endpoint"), pl.col("Media")
    )
    inter_reusability_criteria = latex_output.select(
        pl.col("Identifier"),
        pl.col("Data model"),
        pl.col("License"),
        pl.col("Provenance"),
    )
    # GT(latex_output)
    # print(GT(findability_criteria).as_latex())
    # considered_sources
    inter_reusability_criteria
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Knowledge Graph Analysis
    """)
    return


@app.cell
def _(VkgSchematicWidget, mo):
    vkg_schematic = mo.ui.anywidget(VkgSchematicWidget())
    mo.md(
        f"""## From heterogeneous sources to a virtual knowledge graph
    {vkg_schematic}
    <p style="text-align: center;">Sources are mapped to a shared ontology and queried through a single SPARQL interface.</p>"""
    )
    return


@app.cell
def _(List, Path, Tuple, data_folder, glob, mo):
    __CHIO = "https://dlr-ve-esy.github.io/charging-ontology/"
    VKG = "https://gitlab.dlr.de/vkg#"

    paths: List[Path] = [Path(f) for f in glob(f"{data_folder}/*")]
    mappings: List[Tuple[str, str]] = [(m.name, m.as_posix()) for m in paths]

    # load ottr templates for expansion
    with open("templates/evse.stottr", "r") as input_a:
        vkg_evse = input_a.read()
    with open("templates/common.stottr", "r") as input_b:
        vkg_common = input_b.read()

    snippet = "\n".join(vkg_evse.split("\n")[13:22])
    mo.md(
        f"""## Graph is expanded using OTTR templates

    The original sources are converted to a common tabular model which is expanded to a graph. For example, with this template we expand the data from a EVSE.
    ```
    {snippet}
    ```
    Each comand expands to different patterns.
    """
    )
    return VKG, vkg_common, vkg_evse


@app.cell
def _(Path, config, data_folder, mo, pl):
    # Source selection is persisted in run_config.yaml (analysis
    # inclusion and exclusion reasons), not in notebook checkbox
    # state. de.1 is excluded from the German quantitative comparison
    # to prevent overlap with de.2 (both German datasets would
    # double-count German EVSEs); the exclusion and its reason are
    # recorded in the manifest.
    parsed_dirs = {
        p.name: p.as_posix() for p in Path(data_folder).iterdir() if p.is_dir()
    }
    selected_sources = []
    missing_parsed = []
    for _entry in config.analysis_datasets():
        if _entry.parsed_dir is None:
            continue
        if _entry.parsed_dir in parsed_dirs:
            selected_sources.append(
                (_entry.parsed_dir, parsed_dirs[_entry.parsed_dir])
            )
        else:
            missing_parsed.append(_entry.dataset_id)

    selection_table = mo.ui.table(
        data=pl.DataFrame(
            [
                {
                    "dataset_id": d.dataset_id,
                    "snapshot_id": d.snapshot_id,
                    "snapshot_date": str(d.snapshot_date or ""),
                    "included": d.include_in_analysis,
                    "coverage": ", ".join(d.country_coverage),
                    "exclusion_reason": d.exclusion_reason or "",
                }
                for d in config.datasets
            ]
        ),
        show_column_summaries=False,
        show_download=False,
    )
    warning = (
        f"WARNING: parsed output missing for {', '.join(missing_parsed)}. "
        "Run `uv run python extract_data.py` to extract the configured "
        "inputs before expanding the graph."
        if missing_parsed
        else ""
    )
    mo.md(
        f"""## Configured source selection

    {selection_table}

    {warning}"""
    )
    return (selected_sources,)


@app.cell
def _(
    Mapping,
    config,
    expand_bnezta,
    expand_relational_csv,
    selected_sources,
    vkg_common,
    vkg_evse,
):
    m = Mapping([vkg_common, vkg_evse])
    for name, path in selected_sources:
        entry = config.entry_by_parsed_dir(name)
        country = entry.country
        # Explicit per-source country coverage from the run
        # configuration. The NOBIL filter lists NO, DK, FI, IS and SE
        # explicitly, so no country can be silently reset (the
        # historical if/else overwrote the Norwegian filter through
        # its else branch). National single-country publications keep
        # their historical unfiltered expansion; AT keeps its
        # historical ["AT"] filter.
        if entry.format in ("datex2", "nobil", "irve"):
            print(entry)
            expand_relational_csv(
                "graph",
                path,
                m,
                challenge=False,
                country=country,
                country_filter=entry.expansion_country_filter,
            )
        elif entry.format == "bnetza":
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
        p.parent.mkdir(exist_ok=True)
        response = requests.get(ONTOLOGY_IRI)
        if response.status_code == 200:
            with open(p, "wb") as onto_file:
                onto_file.write(response.content)

    qr = pyqrcode.create("https://dlr-ve-esy.github.io/charging-ontology/")
    Path("public").mkdir(exist_ok=True)
    img = "public/qr-code.png"
    qr.png(img, scale=5)

    m.read_triples("ontology/chio-full.ttl", transient=False, graph=TEST_GRAPH)
    mo.md(
        """## Load Ontology into graph and perform reasoning

    The charging ontology is in GitHub and it is hosted as a static site
    <p style="justify-content: space-evenly; display: flex;"><a href="https://github.com/dlr-ve-esy/charging-ontology" rel="noopener" target="_blank"><img alt="dlr-ve-esy/charging-ontology - GitHub" src="https://gh-card.dev/repos/dlr-ve-esy/charging-ontology.svg"></a><img src="public/qr-code.png" width="100"/></p>"""
    )
    return (TEST_GRAPH,)


@app.cell
def _(mo):
    mo.md("""
    ## Visual summary of ontological commitments

    <p style="justify-content: space-evenly; display: flex;"><img src="public/mereology-summary.png"/></p>
    """)
    return


@app.cell
def _(TEST_GRAPH, m, mo):
    with open("reasoning/charging_connector.sparql", "r") as input_c:
        charging_connector = input_c.read()

    m.insert(charging_connector, target_graph=TEST_GRAPH, source_graph=TEST_GRAPH)
    mo.md(
        f"""## Perform reasoning

    In theory, we could try to infer all the axioms of the graph, but doing so would consume a lot of memory. We only need a handful of inferences so we perform them individually.

    ### Infer connector class

    We find everything that is being assigned to a subclass of connector and  assign it the connector class
    ```sparql
    {charging_connector}
    ```"""
    )
    return


@app.cell
def _(TEST_GRAPH, m, mo):
    with open("reasoning/has_part.sparql", "r") as input_d:
        has_part = input_d.read()
    m.insert(has_part, target_graph=TEST_GRAPH, source_graph=TEST_GRAPH)
    mo.md(
        f"""### Mereology: "has part" is inverse of "part of"

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
    ```"""
    )
    return


@app.cell
def _(TEST_GRAPH, m, mo):
    with open("reasoning/part_of.sparql", "r") as input_g:
        part_of = input_g.read()
    m.insert(part_of, target_graph=TEST_GRAPH, source_graph=TEST_GRAPH)
    mo.md(
        f"""### Mereology: "part of" is transitive

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
    """
    )
    return


@app.cell
def _(mo):
    mo.md("""
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
    """)
    return


@app.cell
def _(mo):
    with open(
        "queries/total_aggregated_power_per_country_lower.sparql", "r"
    ) as input_e:
        total_aggregated_power_per_country_lower = input_e.read()
    mo.md(
        f"""## Perform queries

    ### Total power accounting minimum EVSE potential 

    ```sparql
    {total_aggregated_power_per_country_lower}
    ```"""
    )
    return (total_aggregated_power_per_country_lower,)


@app.cell
def _(
    TEST_GRAPH,
    country_codes,
    df_to_dict,
    em,
    m,
    target_tracker,
    total_aggregated_power_per_country_lower,
):
    aggregated_power_df = m.query(
        total_aggregated_power_per_country_lower, graph=TEST_GRAPH
    )
    study_filter = list(aggregated_power_df["code"].unique())

    # Calculated-led join (error_metrics.build_results_frame): every
    # country with a calculated power stays in the frame even when the
    # EAFO reports no reference power or AFIR target (IS, NO). Missing
    # references and targets stay missing; nothing is filled with
    # zero, so a failed or unavailable calculation cannot appear as
    # measured zero capacity.
    results = em.build_results_frame(
        aggregated_power_df, target_tracker, country_codes
    )

    # AFIR target markers only where a target exists.
    filtered_markers = {
        k: v
        for k, v in df_to_dict(results, key_col="Code", value_col="target_mw").items()
        if v is not None
    }
    return aggregated_power_df, filtered_markers, results, study_filter


@app.cell
def _(GroupedBarChartWidget, df_to_dict, filtered_markers, mo, results):
    # Grouped side-by-side bars (calculated vs EAFO reference) instead
    # of the former overlapping front/shadow design; colour fills,
    # hatched shadow series, AFIR target markers retained.
    results_plot = GroupedBarChartWidget(
        input=df_to_dict(results, key_col="Code", value_col="total_accounted_power"),
        shadow=df_to_dict(results, key_col="Code", value_col="total_mw"),
        markers=filtered_markers,
        bar_radius=4,
        bar_color="#0173b2",
        marker_color="#353839",
        shadow_color="#d55e00",
        width=539 * 2,  # 539   for elsevier size
        height=202 * 2,  # 202 for elsevier size
        y_max=10000,
        y_ticks=[2000, 4000, 6000, 8000],
        y_grid=[2000, 4000, 6000, 8000],  # Uncomment for paper print
        y_label="Power (MW)",
        offset=25,
        font_size=1.0,
        main_label="Calculated",
        shadow_label="EAFO reference",
        marker_label="AFIR target",
        margin={
            "top": 17,
            "right": 0,
            "bottom": 39,
            "left": 33,  # 45,
        },  # left 33, right 0 for paper
    )

    power_plot_widget = mo.ui.anywidget(results_plot)
    mo.md(
        f"""### Total power accounting minimum EVSE potential 

    {power_plot_widget}"""
    )
    return


@app.cell
def _():
    with open("queries/total_evses_per_power.sparql", "r") as input_f:
        total_evses_per_power = input_f.read()
    # mo.md(f"""### EVSE counts per connector power band

    # ```sparql
    # {total_evses_per_power}
    # ```""")
    return (total_evses_per_power,)


@app.cell
def _(TEST_GRAPH, m, pl, study_filter, total_evses_per_power):
    total_evses_per_power_df = m.query(total_evses_per_power, graph=TEST_GRAPH)
    total_evses_per_power_df = (
        total_evses_per_power_df.pivot("power_bin", index="code", values="evse_count")
        .select(
            [
                "code",
                "0-7,4 kW",
                "7,4-22 kW",
                "22-50 kW",
                "50-150 kW",
                "150-350 kW",
                "350+ kW",
            ]
        )
        .filter(pl.col("code").is_in(study_filter))
        .sort(by="code")
    )
    return (total_evses_per_power_df,)


@app.cell
def _(total_evses_per_power_df):
    # Band palette with hatching so the bands stay distinguishable
    # even in black-and-white print.
    cat_colors = {
        "0-7,4 kW": "#9dc291",
        "7,4-22 kW": "#73a861",
        "22-50 kW": "#527a44",
        "50-150 kW": "#e9cf6f",
        "150-350 kW": "#e0ba2f",
        "350+ kW": "#aa8b1a",
    }
    cat_hatches = {
        "#9dc291": "none",
        "#73a861": "diag",
        "#527a44": "cross",
        "#e9cf6f": "dot",
        "#e0ba2f": "hline",
        "#aa8b1a": "vline",
    }

    chart_input = total_evses_per_power_df.to_dicts()
    return cat_colors, cat_hatches, chart_input


@app.cell
def _(country_codes, pl, study_filter):
    power_counts_tracker = (
        pl.read_csv("viz_data/17.06.2025-eafo-power-counts.csv")
        .join(country_codes, left_on="Category", right_on="Country", how="left")
        .with_columns(
            pl.col("Code").alias("code"),
            pl.col("Slow AC recharging point, single-phase (P < 7.4kW)").alias(
                "0-7,4 kW"
            ),
            pl.col(
                "Medium-speed AC recharging point, triple-phase (7.4kW ≤ P ≤ 22kW)"
            ).alias("7,4-22 kW"),
            pl.sum_horizontal(
                "Fast AC recharging point, triple-phase (P > 22kW)",
                "Slow DC recharging point (P < 50kW)",
            ).alias("22-50 kW"),
            pl.col("Fast DC recharging point (50kW ≤ P < 150kW)").alias("50-150 kW"),
            pl.col(
                "Level 1 - Ultra-fast DC recharging point (150kW ≤ P < 350kW)"
            ).alias("150-350 kW"),
            pl.col("Level 2 - Ultra-fast DC recharging point (P ≥ 350kW)").alias(
                "350+ kW"
            ),
        )
        .select(
            [
                "code",
                "0-7,4 kW",
                "7,4-22 kW",
                "22-50 kW",
                "50-150 kW",
                "150-350 kW",
                "350+ kW",
            ]
        )
        .filter(pl.col("code").is_in(study_filter))
        .sort(by="code")
    )
    chart_input_2 = power_counts_tracker.to_dicts()
    return chart_input_2, power_counts_tracker


@app.cell
def _(
    DoubleStackedBarChartWidget,
    cat_colors,
    cat_hatches,
    chart_input,
    chart_input_2,
    mo,
):
    stacked_chart_3 = DoubleStackedBarChartWidget(
        input_a=chart_input_2,
        input_b=chart_input,
        x_key="code",
        bar_radius=4,
        cat_colors=cat_colors,
        cat_hatches=cat_hatches,
        width=539,  # * 2,  # 539 for elsevier size
        height=202,  #  * 2,  # 202 for elsevier size
        y_label="Counts per capacity",
        x1_label="European Alternative Fuels Observatory, June 2025",
        x2_label="Estimation using available data from the National Access Points",
        offset=38,
        legend_item_width=6.5,
        y_grid=[20000, 90000, 180000],  # Uncoment for journal print
        y_ticks=[20000, 90000, 180000],  # Uncoment for journal print
        y_max=180000,
        font_size=0.9,  # 0.9 for elsevier size
        margin={"top": 15, "right": 0, "bottom": 48, "left": 46},
    )

    stacked_chart_widget = mo.ui.anywidget(stacked_chart_3)

    mo.md(
        f"""### EVSE counts per connector power band

    The calculated bands count DISTINCT EVSEs per connector power band
    (an EVSE with connectors in several bands contributes to each);
    their sum is reported as the EVSE band sum. The EAFO reference
    merges the approximate fast-AC and slow-DC categories into the
    22-50 kW band and distinguishes current types the calculated side
    does not.

    {stacked_chart_widget}"""
    )
    return


@app.cell
def _(config, em, power_counts_tracker, results, total_evses_per_power_df):
    # Shared error calculation (error_metrics.py): the same function
    # feeds the comparison tables, the fidelity heatmap and the
    # exported labels. SPARQL total_accounted_power is the calculated
    # power, EAFO total_mw the reference power; differences are
    # calculated minus reference; the denominator is the EAFO
    # reference for the seven count indicators and the calculated
    # value for power; relative errors are absolute, capped at 1 and
    # averaged only over indicators with a usable error (the coverage
    # is exported next to every mean).
    #
    # "EVSE band sum" is the sum of the per-band DISTINCT-EVSE counts,
    # not an independently deduplicated EVSE total. "Total Power MW"
    # is the sum over EVSEs of the minimum connector power (see
    # queries/total_aggregated_power_per_country_lower.sparql), a
    # minimum-connector aggregation, not guaranteed deliverable power.
    reference_df = em.build_reference_frame(power_counts_tracker, results)
    calculated_df = em.build_calculated_frame(total_evses_per_power_df, results)
    error_table = em.compute_error_table(reference_df, calculated_df)
    fidelity = em.fidelity_summary(error_table)
    relative_error = em.heatmap_frame(error_table, fidelity)

    # Descriptive labels with evidence and provenance (N/A reasons
    # separate from computed Low outcomes; SE/FI marked as NOBIL
    # source substitutions).
    fidelity_labels = em.fidelity_labels_for(fidelity, config)

    value_cols = em.BANDS
    summary_cols = [em.BAND_SUM, em.POWER]
    return (
        calculated_df,
        error_table,
        fidelity,
        fidelity_labels,
        reference_df,
        relative_error,
        summary_cols,
        value_cols,
    )


@app.cell
def _(GT, calculated_df, reference_df, value_cols):
    # Comparison table from the same shared frames as the error
    # calculation: calculated vs EAFO reference per power band.
    comparison_df = calculated_df.join(reference_df, on="code", how="left")
    table_caps = GT(
        comparison_df.select(
            ["code"] + value_cols + [f"{vcc}_right" for vcc in value_cols]
        )
    )
    col_labels = {"code": "Country"}

    for vct in value_cols:
        table_caps = table_caps.tab_spanner(label=vct, columns=[vct, f"{vct}_right"])
        col_labels[vct] = "Calc."
        col_labels[f"{vct}_right"] = "Ref."

    table_caps = table_caps.cols_label(col_labels)
    print(table_caps.as_latex())
    return (comparison_df,)


@app.cell
def _(GT, comparison_df, pl, results, summary_cols):
    # Quantities table from the shared frames: calculated vs EAFO
    # reference vs AFIR target. IS/NO keep their calculated power with
    # missing reference/target entries (no zero fill).
    quantities_df = (
        comparison_df.select(
            ["code"] + summary_cols + [f"{sc}_right" for sc in summary_cols]
        )
        .join(
            results.select(pl.col("Code").alias("code"), pl.col("target_mw")),
            on="code",
            how="left",
        )
        .with_columns(pl.col("target_mw").alias("Target MW"))
        .drop("target_mw")
    )

    table_qs = GT(quantities_df)
    col_labelssc = {"code": "Country"}

    for scs in summary_cols:
        colscss = [scs, f"{scs}_right"]
        if scs == "Total Power MW":
            colscss.append("Target MW")
            col_labelssc["Target MW"] = "Target"
        table_qs = table_qs.tab_spanner(label=scs, columns=colscss)
        col_labelssc[scs] = "Calc."
        col_labelssc[f"{scs}_right"] = "Ref."

    table_qs = table_qs.cols_label(col_labelssc)
    print(table_qs.as_latex())
    return


@app.cell
def _(results):
    results
    return


@app.cell
def _(HeatMapWidget, mo, relative_error):
    hm_colors = {
        "0-7,4 kW": "#6181ab",
        "7,4-22 kW": "#6181ab",
        "22-50 kW": "#6181ab",
        "50-150 kW": "#6181ab",
        "150-350 kW": "#6181ab",
        "350+ kW": "#6181ab",
        "Total Power MW": "#c1a2bb",
        "EVSE band sum": "#e0ba2f",
        "Overall Fidelity": "#73a861",
    }

    hm_widget = mo.ui.anywidget(
        HeatMapWidget(
            input=relative_error.to_dicts(),
            x_axis="code",
            y_axis="range",
            c_axis="cat",
            colors=hm_colors,
            cell_size=11,  # 30
            x_padding=0.0,
            base_color="#F5F5F5",
            width=255,  # 539
            height=152,  # 404
            margin={
                "top": 4,
                "right": 0,
                "bottom": 9,
                "left": 78,
            },
            # margin={
            #     "top": 10,
            #     "right": 0,
            #     "bottom": 48,
            #     "left": 115,
            # },
            font_size=0.9,
            invert_c=False,
            radius=2,  # 5
        )
    )

    mo.md(
        f"""### Quantifying Fidelity

    {hm_widget}
    We estimated the relative error from our estimation against the EAFO reports and inverted it. The lower the error, the higher the fidelity.
    """
    )
    return


@app.cell
def _(pl, relative_error, total_data):
    scatter_df = (
        relative_error.filter(pl.col("range") == "Overall Fidelity")
        .join(
            pl.DataFrame([{"code": k, "score": v} for k, v in total_data.items()]),
            how="left",
            on="code",
        )
        .with_columns(pl.col("score").fill_null(0))
    )
    return (scatter_df,)


@app.cell
def _(pl, scatter_df):
    def assign_points_to_grid(points, n, m, resolve_by="x"):
        x_min, x_max = min(p[0] for p in points), max(p[0] for p in points)
        y_min, y_max = min(p[1] for p in points), max(p[1] for p in points)

        cell_width = (x_max - x_min) / m
        cell_height = (y_max - y_min) / n

        grid = [[None for _ in range(m)] for _ in range(n)]

        for x, y, c in points:
            col = int((x - x_min) / cell_width)
            row = int((y - y_min) / cell_height)
            col = min(col, m - 1)
            row = min(row, n - 1)
            if grid[row][col] is None:
                grid[row][col] = (x, y, c, col, row)
            else:
                existing_point = grid[row][col]
                if x > existing_point[0]:
                    grid[row][col + 1] = (x, y, c, +1, row)
                    continue
                if y > existing_point[1]:
                    grid[row + 1][col] = (x, y, c, col, row + 1)
                    continue

        return grid

    points = [
        (k["error"], k["score"], k["code"])
        for k in scatter_df.with_columns(
            pl.col("error"), pl.col("score").fill_null(0)
        ).to_dicts()
    ]
    nn = 7
    mm = 7

    grid = assign_points_to_grid(points, nn, mm, resolve_by="x")
    # Grid cells store (x, y, code, column, row): the column index derives
    # from the points' x value (fidelity error) and the row index from the
    # points' y value (FAIR score). The widget's horizontal axis ("x")
    # therefore carries the error bin and the vertical axis ("y") the
    # score bin, matching the axis labels below.
    grid_info = []
    for row in grid:
        for col in row:
            if col is not None:
                grid_info.append(
                    {
                        "x": col[3],
                        "y": col[4],
                        "code": col[2],
                    }
                )
    return grid_info, mm, nn


@app.cell
def _(GridScatterWidget, grid_info, mm, mo, nn):
    level_colors = [
        "#d97c78",
        "#e9cf6f",
        "#9dc291",
    ]

    x_vals = [g["x"] for g in grid_info]
    x_domain = list(range(min(x_vals), max(x_vals) + 1, 1))
    y_vals = [g["y"] for g in grid_info]
    y_domain = list(range(min(y_vals), max(y_vals) + 1, 1))

    total_scores = {i["code"]: i["x"] + i["y"] for i in grid_info}

    bin_number = 3
    max_score = nn + mm - 2
    bin_size = (max_score + 1) // bin_number
    top = max_score % bin_size
    region_level = {}

    for r, s in total_scores.items():
        for i, vv in enumerate(range(bin_size, max_score, bin_size)):
            if s <= vv:
                region_level[r] = level_colors[i]
                break
            region_level[r] = level_colors[-1]
    general_widget = mo.ui.anywidget(
        GridScatterWidget(
            input=grid_info,
            x_domain=x_domain,
            y_domain=y_domain,
            x_axis="x",
            y_axis="y",
            color_col="code",
            y_label="FAIR alignment",
            x_label="Quantity fidelity",
            cell_size=25,
            x_padding=0.0,
            base_color="grey",
            width=255,  # 255
            height=int(255 * 0.9),  # 152
            margin={"top": 20, "right": 0, "bottom": 25, "left": 0},
            font_size=1.0,
            cell_ycorrection=2,
            colors=region_level,
        )
    )
    # For paper version use the search function in VSCode and replace the rem with absolute values.
    mo.md(
        f"""### Ordering European states based on performance

    {general_widget}
    """
    )
    return region_level, x_domain, y_domain


@app.cell
def _(
    Path,
    aggregated_power_df,
    cat_colors,
    chart_input,
    chart_input_2,
    error_table,
    fidelity,
    fidelity_labels,
    filtered_markers,
    grid_info,
    json,
    region_level,
    relative_error,
    results,
    total_evses_per_power_df,
    x_domain,
    y_domain,
):
    dump_dir = Path("viz_data/query_results")
    dump_dir.mkdir(parents=True, exist_ok=True)
    dumps = {
        "aggregated_power": aggregated_power_df,
        "total_evses_per_power": total_evses_per_power_df,
        "results": results,
        "relative_error": relative_error,
        "error_table": error_table,
        "fidelity_summary": fidelity,
        "fidelity_labels": fidelity_labels,
        "filtered_markers": filtered_markers,
        "cat_colors": cat_colors,
        "chart_input": chart_input,
        "chart_input_2": chart_input_2,
        "grid_info": grid_info,
        "x_domain": x_domain,
        "y_domain": y_domain,
        "region_level": region_level,
    }
    for _name, _obj in dumps.items():
        if hasattr(_obj, "to_dicts"):
            _obj = _obj.to_dicts()
        with open(dump_dir / f"{_name}.json", "w", encoding="utf-8") as _f:
            json.dump(_obj, _f, ensure_ascii=False, indent=2)
    return


if __name__ == "__main__":
    app.run()
