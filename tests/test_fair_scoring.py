"""Regression tests for the FAIR scoring and dataset selection.

Audit items covered: the Austrian provenance correction (R=3, total
12), the licence prerequisite for provenance points, stable dataset
IDs with both German datasets separate, deterministic latest-record
selection by parsed date, and the country view's documented selection
rule.
"""

import polars as pl

import canonical_values as cv
import fair_scoring as fs


def base_record(**overrides):
    record = {
        "metadata_url": "https://example.org",
        "access_url": "https://data.example.org",
        "actionable": True,
        "medium": "ARCHIVE",
        "access": "OPEN",
        "standard": "DATEXII",
        "license": "CC-BY-4.0",
        "provenance": "EU",
    }
    record.update(overrides)
    return record


def test_austrian_provenance_scores_reusability():
    scores = fs.score_record(base_record(provenance="AT"))
    assert scores["R"] == 3
    assert scores["TOTAL"] == 12


def test_provenance_points_require_licence():
    scores = fs.score_record(base_record(provenance="AT", license=None))
    assert scores["R"] == 0


def test_textual_provenance_scores_lower_than_legal():
    legal = fs.score_record(base_record(provenance="AT"))
    textual = fs.score_record(base_record(provenance="TEXTUAL"))
    assert legal["R"] == 3
    assert textual["R"] == 2


def test_dataset_scores_reproduce_published_table():
    scores = fs.dataset_scores(fs.load_sources())
    assert scores.height == 23
    by_id = {r["dataset_id"]: r for r in scores.to_dicts()}
    for dataset_id, (country, _, f, a, i, r) in cv.FAIR_DATASET_SCORES.items():
        row = by_id[dataset_id]
        assert (row["F"], row["A"], row["I"], row["R"]) == (f, a, i, r)
        assert row["TOTAL"] == f + a + i + r


def test_at_total_is_twelve():
    scores = fs.dataset_scores(fs.load_sources())
    at = scores.filter(pl.col("dataset_id") == "at.1").to_dicts()[0]
    assert (at["F"], at["A"], at["I"], at["R"]) == (3, 3, 3, 3)
    assert at["TOTAL"] == 12


def test_both_german_datasets_are_separate():
    scores = fs.dataset_scores(fs.load_sources())
    ids = set(scores["dataset_id"].to_list())
    assert {"de.1", "de.2"} <= ids
    de1 = scores.filter(pl.col("dataset_id") == "de.1").to_dicts()[0]
    de2 = scores.filter(pl.col("dataset_id") == "de.2").to_dicts()[0]
    assert de1["snapshot_id"] != de2["snapshot_id"]


def test_latest_record_selection_is_deterministic():
    sources = fs.load_sources()
    at_rows = sources.filter(pl.col("dataset_id") == "at.1")
    assert at_rows.height == 2  # January and September assessment records
    latest1 = fs.latest_record_per_dataset(sources)
    latest2 = fs.latest_record_per_dataset(sources)
    assert latest1.to_dicts() == latest2.to_dicts()
    at_latest = latest1.filter(pl.col("dataset_id") == "at.1").to_dicts()[0]
    assert at_latest["id"] == "AT-20250904-ECONTROL-DATEXII"


def test_country_view_matches_published_totals():
    scores = fs.dataset_scores(fs.load_sources())
    analysis_ids = ["at.1", "cy.1", "de.2", "es.1", "fr.1", "lv.1", "no.1", "pt.1", "si.1"]
    view = fs.country_view(scores, analysis_ids)
    assert view["DE"]["TOTAL"] == 7  # de.2 represents Germany
    assert view["AT"]["TOTAL"] == 12
    for country, total in cv.FAIR_COUNTRY_TOTALS.items():
        assert view[country]["TOTAL"] == total, country
