"""Export the figure widgets as PNGs sized for a journal paper.

Each widget is instantiated with its paper configuration, the widget's
trait values are serialized into a mock model (the JavaScript modules
only call ``model.get``), embedded in a minimal HTML page, and
screenshotted with a headless Chromium-based browser (Edge by default).

The widget dimensions follow the "for paper" comments in main.py
(single-column Elsevier figures are ~539px wide at the notebook's scale).
PNGs are captured with a device scale factor so the output is crisp in
print: 539px * 3 = 1617px, which is ~314 DPI at the manuscript's full
text width (\\textwidth = 130.8 mm) and ~419 DPI at 0.75\\textwidth
(98.1 mm) -- above the 300 DPI print target in both cases.

Before rendering, the figure inputs in viz_data/ are asserted against
the published manuscript tables (canonical_values.py); the export fails
if any value deviates.

Usage:
    uv run python export_widget_pngs.py [--output images] [--scale 3]
        [--only fair_barcharts ...] [--browser PATH] [--no-paper]

Paper figures land in <output>/paper/ under the manuscript's filenames
(figure_1.png, figure_2.png, figure_4.png, figure_5.png, figure_6.png);
pass --no-paper to skip that step.

Requires internet access (the widget modules import d3 from esm.sh) and
a Chromium-based browser. Widgets whose input data is computed by graph
queries in the notebook read from viz_data/query_results, which the
notebook's dump cell writes and which is committed to the repo.
"""

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import polars as pl

import canonical_values as cv
from widgets.barchart import (
    BarChartWidget,
    DoubleStackedBarChartWidget,
    FAIRBarChartsWidget,
    FAIRDatasetScoresWidget,
    GroupedBarChartWidget,
)
from widgets.cartogram import SourcesCartogramWidget, FAIRCartogramWidget
from widgets.grid_scatter import GridScatterWidget
from widgets.heatmap import HeatMapWidget

ROOT = Path(__file__).resolve().parent
WIDGETS_JS = ROOT / "widgets" / "javascript"

DEFAULT_BROWSER = Path(
    "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
)

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
html, body {{
    margin: 0;
    padding: 0;
    background: #ffffff;
}}
#widget {{
    width: {width}px;
    height: {height}px;
}}
.cartogram {{
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    width: 100%;
}}
.cartogram svg {{
    max-width: 100%;
    max-height: 100%;
}}
.barchart {{
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    width: 100%;
}}
.barchart svg {{
    max-width: 100%;
    max-height: 100%;
}}
.fair-barcharts {{
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    width: 100%;
}}
.fair-barcharts svg {{
    max-width: 100%;
    max-height: 100%;
}}
.fair-datasets {{
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    width: 100%;
}}
.fair-datasets svg {{
    max-width: 100%;
    max-height: 100%;
}}
.heatmap {{
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    width: 100%;
}}
.heatmap svg {{
    max-width: 100%;
    max-height: 100%;
}}
.scatter {{
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    width: 100%;
}}
.scatter svg {{
    max-width: 100%;
    max-height: 100%;
}}
</style>
</head>
<body>
<div id="widget"></div>
<script type="module">
{module_source}
const state = {state};
const model = {{ get: (name) => state[name] }};
const el = document.getElementById("widget");
await render({{ model, el }});
</script>
</body>
</html>
"""


def widget_to_state(widget) -> dict:
    """All JSON-serializable trait values of a widget.

    Mirrors what ``model.get`` returns in the notebook: traits that are
    not explicitly configured fall back to the widget class defaults.
    """
    state = {}
    for name in type(widget).class_trait_names():
        if name.startswith("_"):
            continue
        value = getattr(widget, name)
        try:
            json.dumps(value)
        except (TypeError, ValueError):
            continue
        state[name] = value
    return state


def load_json(name):
    with open(ROOT / "viz_data" / name, "r", encoding="utf-8") as f:
        return json.load(f)


def assert_canonical_inputs() -> None:
    """M-3 guard: figure inputs must reproduce the published tables.

    This is the check that would have caught the stale Figure 5 and the
    later re-run whose values diverged from the published analysis
    state. Raises AssertionError on any deviation.
    """
    cv.assert_fair_country_scores(load_json("fair_scores.json"))
    cv.assert_dataset_scores(load_json("fair_scores_datasets.json"))
    cv.assert_results(load_json("query_results/results.json"))
    cv.assert_band_counts(
        load_json("query_results/chart_input.json"),
        cv.PUBLISHED_CAPACITIES_CALC,
        "query_results/chart_input.json",
    )
    cv.assert_band_counts(
        load_json("query_results/chart_input_2.json"),
        cv.PUBLISHED_CAPACITIES_REF,
        "query_results/chart_input_2.json",
    )
    cv.assert_filtered_markers(load_json("query_results/filtered_markers.json"))


# Manuscript float -> exported widget mapping (guide M-2). figure_3,
# figure_8 and the VKG schematic are not products of this repository.
PAPER_FIGURES = {
    "figure_1.png": "sources_cartogram.png",  # fig:eafo-sources
    "figure_2.png": "fair_dataset_scores.png",  # fig:fair-summary
    "figure_4.png": "results_plot.png",  # fig:capacity-comparison
    "figure_5.png": "capacities_merged.png",  # fig:power-capacity
    "figure_6.png": "power_counts_stacked.png",  # fig:device-counts
}


def df_to_dict(df: pl.DataFrame, key_col: str, value_col: str) -> dict:
    """Get a Python dict from two columns of a DataFrame.

    If the key column is not unique, the last row is used.
    """
    return dict(df.select(key_col, value_col).iter_rows())


def build_specs() -> list:
    """Widget instances at paper dimensions, mirroring main.py."""
    sources_per_country = load_json("sources_per_country.json")
    source_colors = load_json("source_colors.json")
    color_legend = load_json("color_legend.json")
    country_grid = load_json("countries_9x9_xy.json")
    fair_scores = load_json("fair_scores.json")
    spectrum_colors = load_json("spectrum_colors.json")

    specs = []

    # Sources cartogram: notebook uses 1.3x screen size, paper uses the
    # class defaults (539x404, marker_size 18).
    specs.append(
        {
            "name": "sources_cartogram",
            "module": WIDGETS_JS / "sources_cartogram.js",
            "widget": SourcesCartogramWidget(
                sources_per_country=sources_per_country,
                source_colors=source_colors,
                color_legend=color_legend,
                country_grid=country_grid,
                width=539,
                height=404,
                marker_size=18,
                marker_size_secondary=6,
                legend_marker_size=9,
                legend_height=20,
            ),
        }
    )

    # FAIR cartogram at class default paper size.
    specs.append(
        {
            "name": "fair_cartogram",
            "module": WIDGETS_JS / "fair_score_cartogram.js",
            "widget": FAIRCartogramWidget(
                fair_scores=fair_scores,
                source_colors=spectrum_colors,
                country_grid=country_grid,
                width=539,
                height=404,
            ),
        }
    )

    # FAIR principle grid (2x2) + total score chart, scaled from the 700px
    # design width to the 539px paper width.
    specs.append(
        {
            "name": "fair_barcharts",
            "module": WIDGETS_JS / "fair_score_barcharts.js",
            "widget": FAIRBarChartsWidget(
                fair_scores=fair_scores,
                source_colors=spectrum_colors,
                width=539,
                height=int(640 * 539 / 700),
                bar_radius=4,
                font_size=0.8,
            ),
        }
    )

    # Total FAIR score bar chart: 549x101 for paper.
    total_data = {
        k: v["TOTAL"]
        for k, v in sorted(
            fair_scores.items(), key=lambda item: item[1]["TOTAL"], reverse=True
        )
        if v["TOTAL"] > 0
    }
    specs.append(
        {
            "name": "fair_total_scores",
            "module": WIDGETS_JS / "barchart.js",
            "widget": BarChartWidget(
                input=total_data,
                bar_radius=4,
                bar_color="#9d6b92",
                width=549,
                height=101,
                y_max=12,
                y_ticks=[3, 6, 9, 12],
                y_grid=[3, 6, 9, 12],
                y_label="Total Score",
                font_size=1.2,
                offset=36,
                margin={"top": 24, "right": 10, "bottom": 30, "left": 30},
            ),
        }
    )

    # Dataset-level FAIR scores (fig:fair-summary, Table 8 unit): one
    # stacked bar per dataset, colour fills plus hatching.
    specs.append(
        {
            "name": "fair_dataset_scores",
            "module": WIDGETS_JS / "fair_dataset_scores.js",
            "widget": FAIRDatasetScoresWidget(
                input=load_json("fair_scores_datasets.json"),
                width=539,
                height=320,
            ),
        }
    )

    # Capacity plots from the EAFO target tracker: 539x101 for paper.
    country_codes = pl.read_csv(ROOT / "viz_data" / "code_mappings.csv")
    target_tracker = (
        pl.read_csv(ROOT / "viz_data" / "17.06.2025-eafo-target-tracker.csv")
        .join(country_codes, left_on="Category", right_on="Country", how="left")
        .select("Category", "Code", "Target kW", "Total power (kW) output")
        .with_columns(
            pl.col("Target kW").floordiv(1000).alias("target_mw"),
            pl.col("Total power (kW) output").floordiv(1000).alias("total_mw"),
        )
    )
    for name, condition, y_max, y_ticks, margin, y_label in [
        (
            "capacities_above_400mw",
            pl.col("total_mw") > 400,
            8000,
            [2000, 4000, 6000, 8000],
            {"top": 22, "right": 10, "bottom": 30, "left": 46},
            "Power (MW)",
        ),
        (
            "capacities_below_400mw",
            pl.col("total_mw") <= 400,
            400,
            [100, 200, 300, 400],
            {"top": 16, "right": 10, "bottom": 28, "left": 46},
            "",
        ),
    ]:
        subset = target_tracker.filter(condition)
        specs.append(
            {
                "name": name,
                "module": WIDGETS_JS / "barchart.js",
                "widget": BarChartWidget(
                    input=df_to_dict(subset, "Code", "total_mw"),
                    markers=df_to_dict(subset, "Code", "target_mw"),
                    bar_radius=4,
                    bar_color="#de8f05",
                    marker_color="#353839",
                    width=539,
                    height=101,
                    y_max=y_max,
                    y_ticks=y_ticks,
                    y_grid=y_ticks,
                    y_label=y_label,
                    offset=36,
                    font_size=0.9,
                    margin=margin,
                ),
            }
        )

    # --- Widgets fed by the notebook query results
    # (dumped to viz_data/query_results by the notebook's dump cell) ---

    def query(name):
        return load_json(f"query_results/{name}.json")

    results = query("results")

    # Results plot (fig:capacity-comparison): grouped side-by-side
    # bars, calculated vs EAFO reference, AFIR target markers retained.
    # Twelve countries including IS/NO (no EAFO bar where no reference
    # exists); colour fills, shadow series hatched.
    specs.append(
        {
            "name": "results_plot",
            "module": WIDGETS_JS / "grouped_barchart.js",
            "widget": GroupedBarChartWidget(
                input={
                    r["Code"]: r["total_accounted_power"] for r in results
                },
                shadow={r["Code"]: r["total_mw"] for r in results},
                markers=query("filtered_markers"),
                bar_radius=4,
                bar_color="#0173b2",
                marker_color="#353839",
                shadow_color="#d55e00",
                width=539,
                height=202,
                y_max=10000,
                y_ticks=[2000, 4000, 6000, 8000],
                y_grid=[2000, 4000, 6000, 8000],
                y_label="Power (MW)",
                offset=25,
                font_size=1.0,
                main_label="Calculated",
                shadow_label="EAFO reference",
                marker_label="AFIR target",
                margin={"top": 22, "right": 10, "bottom": 39, "left": 50},
            ),
        }
    )

    # Double stacked chart (fig:device-counts): 539x202 elsevier size,
    # band palette with hatching.
    specs.append(
        {
            "name": "power_counts_stacked",
            "module": WIDGETS_JS / "double_stacked_barchart.js",
            "widget": DoubleStackedBarChartWidget(
                input_a=query("chart_input_2"),
                input_b=query("chart_input"),
                x_key="code",
                bar_radius=4,
                cat_colors=query("cat_colors"),
                cat_hatches={
                    "#9dc291": "none",
                    "#73a861": "diag",
                    "#527a44": "cross",
                    "#e9cf6f": "dot",
                    "#e0ba2f": "hline",
                    "#aa8b1a": "vline",
                },
                width=539,
                height=202,
                y_label="Counts per capacity",
                x1_label="European Alternative Fuels Observatory, June 2025",
                x2_label="Estimation using available data from the National Access Points",
                offset=38,
                legend_item_width=5.4,
                y_grid=[20000, 90000, 180000],
                y_ticks=[20000, 90000, 180000],
                y_max=180000,
                font_size=0.9,
                margin={"top": 20, "right": 10, "bottom": 60, "left": 52},
            ),
        }
    )

    # Fidelity heatmap: paper size 539x404 with cell 30.
    hm_colors = {
        "0-7,4 kW": "#6181ab",
        "7,4-22 kW": "#6181ab",
        "22-50 kW": "#6181ab",
        "50-150 kW": "#6181ab",
        "150-350 kW": "#6181ab",
        "350+ kW": "#6181ab",
        "Total Power MW": "#c1a2bb",
        "Total EVSE": "#e0ba2f",
        "Overall Fidelity": "#73a861",
    }
    specs.append(
        {
            "name": "fidelity_heatmap",
            "module": WIDGETS_JS / "heatmap.js",
            "widget": HeatMapWidget(
                input=query("relative_error"),
                x_axis="code",
                y_axis="range",
                c_axis="cat",
                colors=hm_colors,
                cell_size=30,
                x_padding=0.0,
                base_color="#F5F5F5",
                width=539,
                height=404,
                margin={"top": 30, "right": 0, "bottom": 48, "left": 115},
                font_size=0.9,
                invert_c=False,
                radius=5,
            ),
        }
    )

    # Performance grid scatter.
    specs.append(
        {
            "name": "performance_grid",
            "module": WIDGETS_JS / "grid_scatter.js",
            "widget": GridScatterWidget(
                input=query("grid_info"),
                x_domain=query("x_domain"),
                y_domain=query("y_domain"),
                x_axis="x",
                y_axis="y",
                color_col="code",
                y_label="FAIR alignment",
                x_label="Quantity fidelity",
                cell_size=25,
                x_padding=0.0,
                base_color="grey",
                width=255,
                height=229,
                margin={"top": 20, "right": 10, "bottom": 25, "left": 10},
                font_size=1.0,
                cell_ycorrection=2,
                colors=query("region_level"),
            ),
        }
    )

    return specs


def export_widget(spec, browser: Path, output_dir: Path, scale: int) -> Path:
    state = widget_to_state(spec["widget"])
    width = state["width"]
    height = state["height"]
    html = HTML_TEMPLATE.format(
        width=width,
        height=height,
        module_source=spec["module"].read_text(encoding="utf-8"),
        state=json.dumps(state),
    )

    png_path = output_dir / f"{spec['name']}.png"

    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / f"{spec['name']}.html"
        html_path.write_text(html, encoding="utf-8")

        cmd = [
            str(browser),
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            "--no-first-run",
            "--no-default-browser-check",
            f"--user-data-dir={tmp}",
            f"--force-device-scale-factor={scale}",
            f"--window-size={width},{height}",
            "--virtual-time-budget=30000",
            f"--screenshot={png_path}",
            html_path.as_uri(),
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )

    if not png_path.exists():
        raise RuntimeError(
            f"Screenshot failed for {spec['name']}: {result.stderr}"
        )
    return png_path


def merge_capacities(output_dir: Path) -> Path:
    """F-4: compose the two capacity exports into one figure file.

    The manuscript float fig:power-capacity spans the >400 MW and the
    <=400 MW panels; the submission package wants one file per figure.
    """
    from PIL import Image

    above = Image.open(output_dir / "capacities_above_400mw.png")
    below = Image.open(output_dir / "capacities_below_400mw.png")
    if above.width != below.width:
        raise RuntimeError(
            f"capacity panels differ in width: {above.width} vs {below.width}"
        )
    merged = Image.new("RGB", (above.width, above.height + below.height), "white")
    merged.paste(above, (0, 0))
    merged.paste(below, (0, above.height))
    merged_path = output_dir / "capacities_merged.png"
    merged.save(merged_path)
    return merged_path


def export_paper_figures(output_dir: Path) -> None:
    """M-2: copy the paper figures under the manuscript's filenames."""
    paper_dir = output_dir / "paper"
    paper_dir.mkdir(parents=True, exist_ok=True)
    for figure_name, source_name in PAPER_FIGURES.items():
        source = output_dir / source_name
        if not source.exists():
            raise RuntimeError(f"missing paper figure input: {source}")
        shutil.copyfile(source, paper_dir / figure_name)
        print(f"paper/{figure_name} <- {source_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Export the figure widgets as PNGs for a journal paper."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "images",
        help="Output directory (default: images)",
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=3,
        help="Device scale factor for the screenshot (default: 3)",
    )
    parser.add_argument(
        "--browser",
        type=Path,
        default=DEFAULT_BROWSER,
        help="Path to a Chromium-based browser executable",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Export only the named widgets",
    )
    parser.add_argument(
        "--no-paper",
        action="store_true",
        help="Skip the manuscript-filename paper figures",
    )
    args = parser.parse_args()

    # M-3: refuse to render from inputs that deviate from the
    # published tables.
    assert_canonical_inputs()
    print("canonical input assertions passed")

    args.output.mkdir(parents=True, exist_ok=True)

    specs = build_specs()
    if args.only:
        specs = [s for s in specs if s["name"] in args.only]

    for spec in specs:
        png = export_widget(spec, args.browser, args.output, args.scale)
        print(f"{spec['name']}: {png}")

    if not args.only or {
        "capacities_above_400mw",
        "capacities_below_400mw",
    }.issubset(set(args.only)):
        merged = merge_capacities(args.output)
        print(f"capacities_merged: {merged}")

    if not args.no_paper:
        export_paper_figures(args.output)


if __name__ == "__main__":
    main()
