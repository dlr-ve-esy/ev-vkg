"""Regression tests for the shared error and fidelity calculation.

Audit items covered: power assignment (calculated vs reference), the
sign convention (calculated minus reference), units (kW to MW), the
denominator convention (EAFO reference for counts, calculated value
for power), the cap at 1, zero-denominator behaviour including 0/0,
reference-only cells, indicator coverage, label boundaries and the
reproduction of the committed canonical outputs.
"""

import json
from pathlib import Path

import polars as pl

import canonical_values as cv
import error_metrics as em
from write_canonical_query_results import canonical_error_outputs

ROOT = Path(__file__).resolve().parent.parent


def canonical_frames():
    """Reference and calculated frames built from the published tables."""
    results = pl.DataFrame(cv.results_records()).with_columns(
        pl.col("Code").alias("code")
    )
    calc_bands = pl.DataFrame(cv.band_records(cv.PUBLISHED_CAPACITIES_CALC))
    ref_bands = pl.DataFrame(cv.band_records(cv.PUBLISHED_CAPACITIES_REF))
    return (
        em.build_reference_frame(ref_bands, results),
        em.build_calculated_frame(calc_bands, results),
    )


def synthetic_frames(ref_rows, calc_rows):
    """Minimal frames from (code, indicator, value) triples.

    Indicators not mentioned are null in both frames, so they surface
    as missing_both rows that contribute nothing to the means.
    """
    def frame(rows):
        data = {"code": [c for c, _, _ in rows]}
        for indicator in em.INDICATORS:
            data[indicator] = [v if ind == indicator else None for _, ind, v in rows]
        return pl.DataFrame(data).with_columns(
            pl.col(indicator).cast(pl.Float64) for indicator in em.INDICATORS
        )

    return frame(ref_rows), frame(calc_rows)


def cell(error_table, code, indicator):
    rows = error_table.filter(
        (pl.col("code") == code) & (pl.col("indicator") == indicator)
    )
    assert rows.height == 1, (code, indicator)
    return rows.to_dicts()[0]


def test_power_assignment_calculated_vs_reference():
    """SPARQL power is the calculated series, EAFO the reference."""
    reference_df, calculated_df = canonical_frames()
    de_calc = calculated_df.filter(pl.col("code") == "DE")[em.POWER][0]
    de_ref = reference_df.filter(pl.col("code") == "DE")[em.POWER][0]
    assert de_calc == 9159
    assert de_ref == 7907


def test_difference_sign_is_calculated_minus_reference():
    error_table = em.compute_error_table(*canonical_frames())
    de = cell(error_table, "DE", em.POWER)
    assert de["calculated"] == 9159
    assert de["reference"] == 7907
    assert de["difference"] == 1252


def test_power_denominator_is_calculated():
    error_table = em.compute_error_table(*canonical_frames())
    de = cell(error_table, "DE", em.POWER)
    assert de["denominator"] == 9159
    assert de["relative_error"] == 1252 / 9159


def test_count_denominator_is_eafo_reference():
    error_table = em.compute_error_table(*canonical_frames())
    at = cell(error_table, "AT", "0-7,4 kW")
    assert at["calculated"] == 1199
    assert at["reference"] == 647
    assert at["denominator"] == 647
    assert at["relative_error"] == abs(1199 - 647) / 647


def test_relative_error_is_absolute_and_capped_at_one():
    ref, calc = synthetic_frames(
        [("XX", em.POWER, 1000)], [("XX", em.POWER, 1)]
    )
    table = em.compute_error_table(ref, calc)
    row = cell(table, "XX", em.POWER)
    assert row["relative_error"] == 1.0


def test_zero_denominator_including_zero_over_zero():
    """0/0 and x/0 yield no relative error and are excluded from means."""
    # XX: 0/0 on power (denominator is the calculated value).
    # YY: 5/0 on a count (denominator is the EAFO reference).
    ref, calc = synthetic_frames(
        [("XX", em.POWER, 0), ("YY", "0-7,4 kW", 0)],
        [("XX", em.POWER, 0), ("YY", "0-7,4 kW", 5)],
    )
    table = em.compute_error_table(ref, calc)
    for code, indicator in (("XX", em.POWER), ("YY", "0-7,4 kW")):
        row = cell(table, code, indicator)
        assert row["status"] == em.STATUS_ZERO_DENOMINATOR
        assert row["relative_error"] is None
    summary = em.fidelity_summary(table)
    assert summary.height == 0


def test_reference_only_count_cell_counts_as_zero():
    """IS and SI >=350 kW references (124, 64) with absent calculated cells."""
    error_table = em.compute_error_table(*canonical_frames())
    is_row = cell(error_table, "IS", "350+ kW")
    si_row = cell(error_table, "SI", "350+ kW")
    assert is_row["reference"] == 124
    assert is_row["calculated"] == 0
    assert is_row["status"] == em.STATUS_REFERENCE_ONLY
    assert is_row["relative_error"] == 1.0
    assert si_row["reference"] == 64
    assert si_row["status"] == em.STATUS_REFERENCE_ONLY
    assert si_row["relative_error"] == 1.0


def test_missing_power_reference_is_not_zero():
    """IS/NO power has no EAFO reference: excluded, never zero-filled."""
    error_table = em.compute_error_table(*canonical_frames())
    for code in ("IS", "NO"):
        row = cell(error_table, code, em.POWER)
        assert row["status"] == em.STATUS_NO_REFERENCE
        assert row["reference"] is None
        assert row["relative_error"] is None


def test_results_frame_keeps_is_and_no_without_reference():
    """Calculated-led join: IS/NO keep calculated power, null reference."""
    aggregated = pl.DataFrame(
        {
            "code": ["DE", "IS", "NO"],
            "total_accounted_power": [9159000.0, 31000.0, 2634000.0],
        }
    )
    tracker = pl.DataFrame(
        {
            "Code": ["DE"],
            "Category": ["Germany"],
            "target_mw": [3139],
            "total_mw": [7907],
        }
    )
    names = pl.DataFrame(
        {
            "Code": ["DE", "IS", "NO"],
            "Country": ["Germany", "Iceland", "Norway"],
        }
    )
    results = em.build_results_frame(aggregated, tracker, names)
    assert results.height == 3
    de = results.filter(pl.col("code") == "DE").to_dicts()[0]
    assert de["total_accounted_power"] == 9159  # kW -> MW
    assert de["total_mw"] == 7907
    assert de["target_mw"] == 3139
    for code, power in (("IS", 31.0), ("NO", 2634.0)):
        row = results.filter(pl.col("code") == code).to_dicts()[0]
        assert row["total_accounted_power"] == power
        assert row["total_mw"] is None
        assert row["target_mw"] is None


def test_indicator_coverage_counts_contributing_indicators():
    error_table = em.compute_error_table(*canonical_frames())
    summary = em.fidelity_summary(error_table)
    by_code = {r["code"]: r for r in summary.to_dicts()}
    assert by_code["DE"]["indicator_coverage"] == 8
    # IS loses only the power indicator (no EAFO reference).
    assert by_code["IS"]["indicator_coverage"] == 7


def test_label_boundaries():
    assert em.fidelity_label(0.0) == "Excellent"
    assert em.fidelity_label(0.40) == "Excellent"
    assert em.fidelity_label(0.4001) == "Good"
    assert em.fidelity_label(0.60) == "Good"
    assert em.fidelity_label(0.6001) == "Low"
    assert em.fidelity_label(1.0) == "Low"
    assert em.fidelity_label(None) == "N/A"


def test_published_labels():
    error_table = em.compute_error_table(*canonical_frames())
    summary = em.fidelity_summary(error_table)
    labels = {
        r["code"]: em.fidelity_label(r["mean_capped_relative_error"])
        for r in summary.to_dicts()
    }
    assert labels["FR"] == "Excellent"
    assert labels["SE"] == "Excellent"
    assert {labels[c] for c in ("AT", "DE", "NO", "PT")} == {"Good"}
    assert {labels[c] for c in ("DK", "ES", "FI", "IS", "LV", "SI")} == {"Low"}


def test_canonical_outputs_match_committed_files():
    heatmap_rows, labels = canonical_error_outputs()
    with open(ROOT / "viz_data/query_results/relative_error.json", encoding="utf-8") as f:
        assert json.load(f) == heatmap_rows
    with open(ROOT / "viz_data/query_results/fidelity_labels.json", encoding="utf-8") as f:
        assert json.load(f) == labels


def test_fidelity_labels_provenance():
    """Labels carry dataset/snapshot provenance and substitution notes."""
    _, records = canonical_error_outputs()
    by_code = {r["code"]: r for r in records}

    # 12 computed labels + 12 N/A entries.
    computed = [r for r in records if r["label"] != "N/A"]
    na = [r for r in records if r["label"] == "N/A"]
    assert len(computed) == 12
    assert len(na) == 12

    # NOBIL substitutions are marked, not presented as measurements.
    for code in ("SE", "FI"):
        assert by_code[code]["source_dataset_id"] == "no.1"
        assert "NOBIL" in by_code[code]["substitution_note"]
        assert "substitution" in by_code[code]["substitution_note"]

    # N/A reasons are explicit and separate from computed Low outcomes.
    for entry in na:
        assert entry["na_reason"]
        assert entry["mean_capped_relative_error"] is None
    assert "CY" in by_code
    assert "no EVSE" in by_code["CY"]["na_reason"]

    # Every computed label carries its evidence and provenance.
    for entry in computed:
        assert entry["mean_capped_relative_error"] is not None
        assert entry["indicator_coverage"] >= 1
        assert entry["source_dataset_id"]
        assert entry["source_snapshot_id"]
