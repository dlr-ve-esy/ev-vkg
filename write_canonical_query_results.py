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

``viz_data/fair_scores.json`` (country level) is already canonical and is
only verified, not rewritten.

Usage:
    uv run python write_canonical_query_results.py
"""

import json
from pathlib import Path

import canonical_values as cv

ROOT = Path(__file__).resolve().parent
VIZ = ROOT / "viz_data"
QUERY = VIZ / "query_results"


def write_json(path: Path, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


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
