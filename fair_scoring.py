"""Shared FAIR scoring and dataset/snapshot selection.

Separates dataset identity from snapshot identity (audit: "Separate
dataset identity from snapshot identity"):

- ``dataset_id`` (at.1, de.1, de.2, ...) is the stable identity of an
  assessed dataset; ``sources/metadata.csv`` records it explicitly.
- The metadata record ``id`` is the snapshot/assessment record id and
  may contain dates; it is never parsed or substring-matched to select
  records.
- The latest assessment record per dataset is selected by
  ``publication_date`` parsed as a date. This selection is distinct
  from quantitative input selection: the latest metadata record need
  not identify the analysis snapshot (run_config.yaml records the
  analysis input separately).

The scoring heuristics are the notebook's documented heuristics, kept
identically (including the licence prerequisite for provenance-based
reusability points and the recognition of Austrian legal provenance
alongside the other accepted national legal frameworks).
"""

from __future__ import annotations

from typing import Any

import polars as pl

ACCESIBLE = ["OPEN", "REGISTERED_USERS", "PER_REQUEST"]
OPTIMAL_ACCESS_MEDIA = ["ARCHIVE", "API"]
INTEROPERABLE_FORMATS = ["OCPI", "OICP", "DATEXII"]
PARTIAL_FORMATS = ["DATEXII_P"]
LEGAL_PROVENANCE = ["EU", "LSV", "AT"]

PRINCIPLES = ["F", "A", "I", "R"]


def score_record(record: dict[str, Any]) -> dict[str, int]:
    """FAIR scores of one assessment record.

    ``record`` is a row of sources/metadata.csv with ``actionable``
    and ``identifier`` already boolean and ``publication_date`` parsed
    as a date.
    """
    scores = {"F": 0, "A": 0, "I": 0, "R": 0}

    # FINDABILITY
    if (record["metadata_url"] is None) and (record["access_url"] is not None):
        if record["medium"] in OPTIMAL_ACCESS_MEDIA:
            scores["F"] = 1
    elif record["metadata_url"] is not None:
        scores["F"] = 2
        if record["actionable"]:
            scores["F"] = 3

    # ACCESIBILITY
    if record["access"] in ACCESIBLE:
        scores["A"] += 1
        if record["medium"] in OPTIMAL_ACCESS_MEDIA:
            scores["A"] += 1
            if record["access_url"] is not None:
                scores["A"] += 1

    # INTEROPERABILITY
    if record["standard"] == "DOCUMENTED":
        scores["I"] += 1
    if record["standard"] in INTEROPERABLE_FORMATS:
        scores["I"] += 3
    if record["standard"] in PARTIAL_FORMATS:
        scores["I"] += 2

    # REUSABILITY: the licence is a prerequisite for the provenance
    # points. Austrian legal provenance (AT) counts alongside the
    # other accepted national legal frameworks (revised assessment
    # correction to the original scorer).
    if record["license"] is not None:
        scores["R"] += 1
        if record["provenance"] == "TEXTUAL":
            scores["R"] += 1
        elif record["provenance"] in LEGAL_PROVENANCE:
            scores["R"] += 2

    scores["TOTAL"] = sum(scores[p] for p in PRINCIPLES)
    return scores


def load_sources(path: str = "sources/metadata.csv") -> pl.DataFrame:
    """Metadata with booleans and dates parsed."""
    sources = pl.read_csv(path, encoding="utf-8")
    return sources.with_columns(
        pl.col("actionable").replace_strict({"NO": False, "YES": True}),
        pl.col("identifier").replace_strict({"NO": False, "YES": True}),
        pl.col("publication_date").str.to_date("%m/%d/%Y"),
    )


def latest_record_per_dataset(sources: pl.DataFrame) -> pl.DataFrame:
    """One assessment record per dataset: the latest by parsed date.

    Deterministic: ties on publication_date keep the last row in file
    order.
    """
    return (
        sources.sort("publication_date", maintain_order=True)
        .group_by("dataset_id", maintain_order=True)
        .last()
    )


def dataset_scores(sources: pl.DataFrame) -> pl.DataFrame:
    """One FAIR score row per assessed dataset (23 rows).

    Both German datasets remain separate (de.1 and de.2); there is no
    country-level ``first()`` selection at the dataset level.
    """
    latest = latest_record_per_dataset(sources)
    rows = []
    for record in latest.iter_rows(named=True):
        scores = score_record(record)
        rows.append(
            {
                "dataset_id": record["dataset_id"],
                "snapshot_id": record["id"],
                "country": record["dataset_id"].split(".")[0].upper(),
                "provider": record["provider"],
                "publication_date": record["publication_date"],
                **scores,
            }
        )
    return pl.DataFrame(rows).sort("dataset_id")


def country_view(
    scores: pl.DataFrame, analysis_dataset_ids: list[str]
) -> dict[str, dict[str, int]]:
    """Country-level FAIR view for the cartogram and total chart.

    Selection rule (documented, deterministic): a country with more
    than one assessed dataset is represented by the dataset included
    in the quantitative comparison (de.2 for Germany, the dataset
    used in the paper's German comparison); a country with a single
    assessed dataset is represented by that dataset. AT's two
    snapshots are one dataset, so no per-country choice arises.
    """
    selected: dict[str, dict[str, int]] = {}
    for country in scores["country"].unique(maintain_order=True):
        country_rows = scores.filter(pl.col("country") == country)
        if country_rows.height > 1:
            included = country_rows.filter(
                pl.col("dataset_id").is_in(analysis_dataset_ids)
            )
            if included.height != 1:
                raise ValueError(
                    f"country {country}: expected exactly one analysis "
                    f"dataset, got {included.height}"
                )
            row = included.to_dicts()[0]
        else:
            row = country_rows.to_dicts()[0]
        selected[country] = {p: row[p] for p in PRINCIPLES + ["TOTAL"]}
    return selected
