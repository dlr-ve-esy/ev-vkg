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

Figure inputs come from the current notebook calculations in
viz_data/query_results/. Rerun main.py after changing the source data.
No published result values are enforced or substituted.

Usage:
    uv run python export_widget_pngs.py [--output images] [--scale 3]
        [--only fair_barcharts ...] [--browser PATH] [--no-paper]

Paper figures land in <output>/paper/ under the manuscript's filenames
(figure_1.png, figure_2.png, figure_4.png, figure_5.png, figure_6.png);
pass --no-paper to skip that step.

Requires internet access (the widget modules import d3 from esm.sh) and
a Chromium-based browser. Widgets whose input data is computed by graph
queries in the notebook read from viz_data/query_results, which the
notebook's dump cell writes and which is intentionally not committed to the repo.
"""

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import polars as pl

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
from widgets.vkg_schematic import VkgSchematicWidget

ROOT = Path(__file__).resolve().parent
WIDGETS_JS = ROOT / "widgets" / "javascript"

def find_browser() -> Path | None:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
    ]
    for name in ("chromium", "chromium-browser", "google-chrome", "microsoft-edge"):
        if executable := shutil.which(name):
            return Path(executable)
    return next((Path(path) for path in candidates if Path(path).is_file()), None)


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


# Manuscript filenames for the figures produced here.
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


def build_specs(only=None, query_dir=None) -> list:
    """Widget instances at paper dimensions, mirroring main.py."""
    selected = set(only) if only is not None else None
    def wants(name):
        return selected is None or name in selected

    query_dir = Path(query_dir) if query_dir is not None else ROOT / "viz_data/query_results"
    def query(name):
        path = query_dir / f"{name}.json"
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing computed figure input: {path}. Run main.py to completion "
                "to regenerate figure inputs from the current data."
            )
        return json.loads(path.read_text(encoding="utf-8"))

    sources_per_country = load_json("sources_per_country.json")
    source_colors = load_json("source_colors.json")
    color_legend = load_json("color_legend.json")
    country_grid = load_json("countries_9x9_xy.json")
    fair_scores = query("fair_scores") if any(wants(n) for n in ("fair_cartogram", "fair_total_scores")) else {}
    spectrum_colors = load_json("spectrum_colors.json")

    specs = []

    # Sources cartogram: notebook uses 1.3x screen size, paper uses the
    # class defaults (539x404, marker_size 18).
    if wants('sources_cartogram'):
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
    if wants('fair_cartogram'):
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

    # FAIR principle grid (2x2) + total score chart for computed source assessments
    #, scaled from the 700px design width to the 539px
    # paper width.
    fair_scores_datasets = query("fair_scores_datasets") if any(wants(n) for n in ("fair_barcharts", "fair_dataset_scores")) else []
    if wants('fair_barcharts'):
        specs.append(
            {
                "name": "fair_barcharts",
                "module": WIDGETS_JS / "fair_score_barcharts.js",
                "widget": FAIRBarChartsWidget(
                    fair_scores={row["code"]: row for row in fair_scores_datasets},
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
    if wants('fair_total_scores'):
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

    # FAIR source-assessment scores: one stacked bar per computed record.
    if wants('fair_dataset_scores'):
        specs.append(
            {
                "name": "fair_dataset_scores",
                "module": WIDGETS_JS / "fair_dataset_scores.js",
                "widget": FAIRDatasetScoresWidget(
                    input=fair_scores_datasets,
                    width=539,
                    height=320,
                ),
            }
        )

    # Capacity plots from the EAFO target tracker: 539x101 for paper.
    if wants("capacities_above_400mw") or wants("capacities_below_400mw"):
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
            if wants(name):
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

    results = query("results") if wants("results_plot") else []

    # Results plot (fig:capacity-comparison): grouped side-by-side
    # bars, calculated vs EAFO reference, AFIR target markers retained.
    # Countries and values follow the current notebook results.
    if wants('results_plot'):
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
                    y_max=max(10000, int(max(
                    [v or 0 for r in results for v in (r["total_accounted_power"], r["total_mw"])]
                    + list(query("filtered_markers").values()) + [0]
                ) * 1.1)),
                    y_ticks=[],
                    y_grid=[],
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
    if wants('power_counts_stacked'):
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
                    y_max=max(180000, int(max(
                    [sum(v for k, v in row.items() if k != "code" and isinstance(v, (int, float)))
                     for row in query("chart_input") + query("chart_input_2")] + [0]
                ) * 1.1)),
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
        "Max Power MW": "#c1a2bb",
        "Total EVSE": "#e0ba2f",
        "Overall Fidelity": "#73a861",
    }
    if wants('fidelity_heatmap'):
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
    if wants('performance_grid'):
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
                    y_label="Quantity fidelity",
                    x_label="FAIR alignment",
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

    if wants("vkg_schematic"):
        specs.append({
            "name": "vkg_schematic",
            "module": WIDGETS_JS / "vkg_schematic.js",
            "widget": VkgSchematicWidget(),
        })
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
        png_path.unlink(missing_ok=True)
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )

    if result.returncode != 0 or not png_path.exists():
        raise RuntimeError(
            f"Screenshot failed for {spec['name']}: {result.stderr}"
        )
    from PIL import Image, ImageChops
    with Image.open(png_path) as screenshot:
        rgb = screenshot.convert("RGB")
        if ImageChops.difference(rgb, Image.new("RGB", rgb.size, "white")).getbbox() is None:
            raise RuntimeError(
                f"Blank screenshot for {spec['name']}; check browser access to esm.sh."
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


def export_paper_figures(output_dir: Path, generated: set[str]) -> None:
    """M-2: copy the paper figures under the manuscript's filenames."""
    paper_dir = output_dir / "paper"
    paper_dir.mkdir(parents=True, exist_ok=True)
    for figure_name, source_name in PAPER_FIGURES.items():
        if source_name not in generated:
            continue
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
        default=find_browser(),
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
    parser.add_argument(
        "--query-dir", type=Path, default=ROOT / "viz_data/query_results",
        help="Computed figure inputs written by main.py",
    )
    args = parser.parse_args()
    if args.scale < 1:
        parser.error("--scale must be positive")
    if args.browser is None or not args.browser.is_file():
        parser.error("No Chromium browser found; provide --browser PATH")
    known = {
        "sources_cartogram", "fair_cartogram", "fair_barcharts", "fair_total_scores",
        "fair_dataset_scores", "capacities_above_400mw", "capacities_below_400mw",
        "results_plot", "power_counts_stacked", "fidelity_heatmap", "performance_grid",
        "vkg_schematic",
    }
    if args.only is not None and (not args.only or set(args.only) - known):
        parser.error("--only requires valid widget names: " + ", ".join(sorted(known)))
    args.output = args.output.resolve()

    args.output.mkdir(parents=True, exist_ok=True)

    specs = build_specs(args.only, args.query_dir)
    if args.only:
        specs = [s for s in specs if s["name"] in args.only]

    generated = set()
    for spec in specs:
        png = export_widget(spec, args.browser, args.output, args.scale)
        generated.add(png.name)
        print(f"{spec['name']}: {png}")

    if not args.only or {
        "capacities_above_400mw",
        "capacities_below_400mw",
    }.issubset(set(args.only)):
        merged = merge_capacities(args.output)
        generated.add(merged.name)
        print(f"capacities_merged: {merged}")

    if not args.no_paper:
        export_paper_figures(args.output, generated)


if __name__ == "__main__":
    main()
