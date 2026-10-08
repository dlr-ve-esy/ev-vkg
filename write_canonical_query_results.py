"""Write the canonical (published) figure inputs into viz_data/.

The notebook's dump cell writes ``viz_data/query_results/*.json`` from
whatever the live queries produce. A later re-run against refetched
sources (September AT refetch, July BNetZA snapshot) produced values that
do NOT reproduce the published tables, so this script restores the
published analysis state (guide items D-1 to D-4):

- ``viz_data/fair_scores_datasets.json``  (new)  Table 8 per dataset
- ``viz_data/query_results/results.json``         Table 6 power columns
- ``viz_data/query_results/chart_input.json``    Table 7 calculated bands
- ``viz_data/query_results/chart_input_2.json``  Table 7 EAFO bands
- ``viz_data/query_results/total_evses_per_power.json`` (same as chart_input)
- ``viz_data/query_results/aggregated_power.json``      (calculated kW)
- ``viz_data/query_results/filtered_markers.json``     (AFIR targets)
- ``viz_data/query_results/relative_error.json``  fidelity heatmap input
- ``viz_data/query_results/fidelity_labels.json`` labels with evidence

``viz_data/fair_scores.json`` (country level) is already canonical and is
only verified, not rewritten.

The fidelity error frame is recomputed from the canonical tables with
the same shared calculation the notebook uses (error_metrics.py). The
previously committed ``relative_error.json`` was stale: it had been
produced by the September AT / July BNetZA re-run and did not
reproduce the published tables (e.g. the German power error was
0.187 instead of the published 1252/9159 = 0.137).

Usage:
    uv run python write_canonical_query_results.py
"""

import json
from pathlib import Path

import polars as pl

import canonical_values as cv
import error_metrics as em
import run_config as rc

ROOT = Path(__file__).resolve().parent
VIZ = ROOT / "viz_data"
QUERY = VIZ / "query_results"


def write_json(path: Path, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def canonical_error_outputs() -> tuple[list, list]:
    """Heatmap rows and fidelity labels derived from the published tables.

    Single implementation shared with export_widget_pngs.py, which
    asserts the committed figure inputs against these values before
    rendering.
    """
    results = pl.DataFrame(cv.results_records()).with_columns(
        pl.col("Code").alias("code")
    )
    calc_bands = pl.DataFrame(cv.band_records(cv.PUBLISHED_CAPACITIES_CALC))
    ref_bands = pl.DataFrame(cv.band_records(cv.PUBLISHED_CAPACITIES_REF))
    reference_df = em.build_reference_frame(ref_bands, results)
    calculated_df = em.build_calculated_frame(calc_bands, results)
    error_table = em.compute_error_table(reference_df, calculated_df)
    summary = em.fidelity_summary(error_table)
    heatmap_rows = em.heatmap_frame(error_table, summary).to_dicts()
    config = rc.load()
    labels = em.fidelity_labels_for(
        summary,
        config,
        na_reason_overrides={
            "CY": (
                "The parsed DATEX II (modified) output contains no EVSE "
                "or connector records, so no calculated values exist."
            )
        },
    )
    return heatmap_rows, labels


def main() -> None:
    QUERY.mkdir(parents=True, exist_ok=True)

    # D-1: verify the country-level canonical file (never rewrite it).
    with open(VIZ / "fair_scores.json", encoding="utf-8") as f:
        cv.assert_fair_country_scores(json.load(f))
    print("fair_scores.json: matches canonical Table 8 (country level)")

    # F-1: dataset-level scores file.
    write_json(VIZ / "fair_scores_datasets.json", cv.dataset_scores_records())
    print("fair_scores_datasets.json: written (23 datasets)")

    # D-2: published results frame.
    write_json(QUERY / "results.json", cv.results_records())
    print("query_results/results.json: written (12 countries)")

    # D-3: published band counts.
    calc_rows = cv.band_records(cv.PUBLISHED_CAPACITIES_CALC)
    ref_rows = cv.band_records(cv.PUBLISHED_CAPACITIES_REF)
    write_json(QUERY / "chart_input.json", calc_rows)
    write_json(QUERY / "chart_input_2.json", ref_rows)
    write_json(QUERY / "total_evses_per_power.json", calc_rows)
    print("query_results/chart_input*.json: written (12 countries)")

    # Calculated power in kW, matching the results frame.
    aggregated = [
        {
            "code": code,
            "total_accounted_power": values[1] * 1000,
        }
        for code, values in cv.PUBLISHED_QUANTITIES.items()
    ]
    write_json(QUERY / "aggregated_power.json", aggregated)
    print("query_results/aggregated_power.json: written")

    # D-4: AFIR targets.
    write_json(QUERY / "filtered_markers.json", cv.filtered_markers())
    print("query_results/filtered_markers.json: written")

    # Fidelity error frame and labels, from the same shared
    # calculation the notebook uses (error_metrics.py). The
    # previously committed relative_error.json was stale (September AT
    # / July BNetZA re-run); this regenerates it from the published
    # tables.
    results = pl.DataFrame(cv.results_records()).with_columns(
        pl.col("Code").alias("code")
    )
    calc_bands = pl.DataFrame(calc_rows)
    ref_bands = pl.DataFrame(ref_rows)
    reference_df = em.build_reference_frame(ref_bands, results)
    calculated_df = em.build_calculated_frame(calc_bands, results)
    error_table = em.compute_error_table(reference_df, calculated_df)
    summary = em.fidelity_summary(error_table)
    write_json(QUERY / "relative_error.json", em.heatmap_frame(error_table, summary).to_dicts())
    print("query_results/relative_error.json: written (12 countries x 9 indicators)")

    config = rc.load()
    labels = em.fidelity_labels_for(
        summary,
        config,
        na_reason_overrides={
            "CY": (
                "The parsed DATEX II (modified) output contains no EVSE "
                "or connector records, so no calculated values exist."
            )
        },
    )
    write_json(QUERY / "fidelity_labels.json", labels)
    print("query_results/fidelity_labels.json: written")

    # Round-trip: everything just written must satisfy the assertions.
    cv.assert_dataset_scores(
        json.load(open(VIZ / "fair_scores_datasets.json", encoding="utf-8"))
    )
    cv.assert_results(
        json.load(open(QUERY / "results.json", encoding="utf-8"))
    )
    cv.assert_band_counts(
        json.load(open(QUERY / "chart_input.json", encoding="utf-8")),
        cv.PUBLISHED_CAPACITIES_CALC,
        "query_results/chart_input.json",
    )
    cv.assert_band_counts(
        json.load(open(QUERY / "chart_input_2.json", encoding="utf-8")),
        cv.PUBLISHED_CAPACITIES_REF,
        "query_results/chart_input_2.json",
    )
    cv.assert_filtered_markers(
        json.load(open(QUERY / "filtered_markers.json", encoding="utf-8"))
    )
    print("all canonical assertions passed")


if __name__ == "__main__":
    main()
