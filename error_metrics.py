"""Shared error and fidelity calculations for the EVSE VKG analysis.

One implementation of the comparison arithmetic, used by the notebook
(main.py), the canonical figure-input writer
(write_canonical_query_results.py) and the regression tests, so that
tables, plots and error inputs cannot disagree on:

- which series is calculated (SPARQL ``total_accounted_power``) and
  which is the reference (EAFO ``total_mw``);
- the sign convention: differences are calculated minus reference;
- the denominator convention: the EAFO reference for the seven count
  indicators, the calculated value for the power indicator;
- the absolute value and the cap of each relative error at 1 before
  averaging;
- which cells contribute to a mean (coverage) and which are excluded.

Policies fixed here (audit: "Centralise and document error
calculations"):

- Indicators without a reference are excluded from the mean; the
  number of contributing indicators is reported next to every mean.
- An absent calculated COUNT cell counts as zero where a reference
  exists (documented historical treatment, e.g. the IS and SI >=350 kW
  reference-only cells). The policy deliberately does NOT extend to
  the power indicator or to missing references: a failed or
  unperformed analysis must not appear as a measured zero.
- A zero denominator (including 0/0) yields no relative error; the
  indicator is excluded from the mean and flagged
  ``zero_denominator``. No published cell has a zero denominator, so
  this policy changes no reported comparison.

Fidelity labels are derived from the mean capped relative error:
Excellent <= 0.40, Good <= 0.60, Low > 0.60. These thresholds were
introduced retrospectively during manuscript revision; they are a
labelling of the numerical comparison, not a new method. The four
qualitative groups of the holistic assessment (Exemplary, Managed,
Operational, Insufficient) are qualitative judgements recorded in the
manuscript and are deliberately NOT derived numerically here.
"""

from __future__ import annotations

import polars as pl

# Power bands of the calculated (SPARQL) side. Boundaries follow
# queries/total_evses_per_power.sparql: inclusive upper bounds except
# the 150-350 kW bin (< 350 kW), so connectors rated exactly 350 kW
# land in "350+ kW". The EAFO reference bands differ at 7.4, 50 and
# 150 kW (half-open intervals); the mapping in
# build_power_counts_tracker documents the merge.
BANDS = [
    "0-7,4 kW",
    "7,4-22 kW",
    "22-50 kW",
    "50-150 kW",
    "150-350 kW",
    "350+ kW",
]

# Sum of the per-band DISTINCT-EVSE counts. This is NOT an
# independently deduplicated EVSE total: an EVSE with connectors in
# more than one power band contributes to several bands.
BAND_SUM = "EVSE band sum"

# Total power is the sum over EVSEs of the minimum connector power
# (queries/total_aggregated_power_per_country_lower.sparql): a
# minimum-connector aggregation, not guaranteed deliverable power and
# not a guaranteed lower bound on installed capacity.
POWER = "Total Power MW"

COUNT_INDICATORS = BANDS + [BAND_SUM]
INDICATORS = COUNT_INDICATORS + [POWER]


def band_of_power(watts: float) -> str:
    """Power band of a connector rating in watts.

    Mirror of the binning in queries/total_evses_per_power.sparql:
    inclusive upper bounds except the 150-350 kW bin (< 350 kW), so a
    connector rated exactly 350 kW lands in "350+ kW". The EAFO
    reference bands differ at 7.4, 50 and 150 kW (half-open
    intervals); harmonising them is a recorded methodological change
    and requires a rerun.
    """
    if watts <= 7400:
        return BANDS[0]
    if watts <= 22000:
        return BANDS[1]
    if watts <= 50000:
        return BANDS[2]
    if watts <= 150000:
        return BANDS[3]
    if watts < 350000:
        return BANDS[4]
    return BANDS[5]

OVERALL = "Overall Fidelity"

# Cell statuses of the error table.
STATUS_OK = "ok"
STATUS_REFERENCE_ONLY = "reference_only"  # absent calculated count cell
STATUS_NO_REFERENCE = "no_reference"  # e.g. IS/NO power
STATUS_NO_CALCULATED = "no_calculated"  # failed/unperformed analysis
STATUS_ZERO_DENOMINATOR = "zero_denominator"  # includes 0/0
STATUS_MISSING_BOTH = "missing_both"


def build_results_frame(
    aggregated_power_df: pl.DataFrame,
    target_tracker: pl.DataFrame,
    country_names: pl.DataFrame,
) -> pl.DataFrame:
    """Calculated-led results frame in MW.

    The join is led by the calculated (SPARQL) side so countries
    without an EAFO power reference or AFIR target (Iceland, Norway)
    keep their calculated power. Missing references and targets stay
    missing; they are never filled with zero. ``aggregated_power_df``
    carries ``total_accounted_power`` in kW, which is converted to MW
    here (the SPARQL query already divided watts by 1000).
    """
    calculated = aggregated_power_df.select(
        pl.col("code"),
        (pl.col("total_accounted_power") / 1000.0).alias("total_accounted_power"),
    )
    reference = target_tracker.select(
        pl.col("Code").alias("code"),
        pl.col("Category").alias("Category"),
        pl.col("target_mw"),
        pl.col("total_mw"),
    )
    names = country_names.select(
        pl.col("Code").alias("code"),
        pl.col("Country").alias("Category"),
    )
    return (
        calculated.join(reference, on="code", how="left")
        .join(names, on="code", how="left", suffix="_name")
        .with_columns(
            pl.coalesce(pl.col("Category"), pl.col("Category_name")).alias("Category"),
            pl.col("code").alias("Code"),
        )
        .drop("Category_name")
        .sort("code")
    )


def build_reference_frame(
    power_counts_tracker: pl.DataFrame, results: pl.DataFrame
) -> pl.DataFrame:
    """EAFO reference frame: EAFO band counts, their sum, EAFO power (MW)."""
    total = pl.sum_horizontal(*BANDS).cast(int).alias(BAND_SUM)
    return (
        power_counts_tracker.with_columns(
            [pl.col(b).cast(int) for b in BANDS] + [total]
        )
        .join(
            results.select(pl.col("code"), pl.col("total_mw")),
            on="code",
            how="left",
        )
        .rename({"total_mw": POWER})
    )


def build_calculated_frame(
    total_evses_per_power_df: pl.DataFrame, results: pl.DataFrame
) -> pl.DataFrame:
    """Calculated frame: SPARQL band counts, their sum, calculated power (MW)."""
    total = pl.sum_horizontal(*BANDS).cast(int).alias(BAND_SUM)
    return (
        total_evses_per_power_df.with_columns(
            [pl.col(b).cast(int) for b in BANDS] + [total]
        )
        .join(
            results.select(
                pl.col("code"), pl.col("total_accounted_power")
            ),
            on="code",
            how="left",
        )
        .rename({"total_accounted_power": POWER})
    )


def _long(frame: pl.DataFrame, value_name: str) -> pl.DataFrame:
    parts = [
        frame.select(
            pl.col("code"),
            pl.lit(indicator).alias("indicator"),
            pl.col(indicator).alias(value_name),
        )
        for indicator in INDICATORS
    ]
    return pl.concat(parts)


def compute_error_table(
    reference_df: pl.DataFrame, calculated_df: pl.DataFrame
) -> pl.DataFrame:
    """Per country and indicator: signed difference, relative error, status.

    Columns: code, indicator, calculated, reference, difference
    (calculated minus reference), denominator, relative_error
    (absolute, capped at 1), status.
    """
    calc_long = _long(calculated_df, "calculated")
    ref_long = _long(reference_df, "reference")

    table = (
        calc_long.join(ref_long, on=["code", "indicator"], how="left")
        .with_columns(pl.col("calculated").alias("calculated_raw"))
        .with_columns(
            # Historical treatment: an absent calculated COUNT cell
            # counts as zero where a reference exists. Absent
            # calculated POWER stays missing (failed analysis).
            pl.when(
                (pl.col("indicator") != POWER)
                & pl.col("calculated_raw").is_null()
                & pl.col("reference").is_not_null()
            )
            .then(pl.lit(0))
            .otherwise(pl.col("calculated_raw"))
            .alias("calculated"),
        )
        .with_columns(
            pl.when(pl.col("indicator") == POWER)
            .then(pl.col("calculated"))
            .otherwise(pl.col("reference"))
            .alias("denominator"),
        )
        .with_columns(
            (pl.col("calculated") - pl.col("reference")).alias("difference"),
        )
        .with_columns(
            pl.when(pl.col("denominator") > 0)
            .then(
                (pl.col("difference").abs() / pl.col("denominator"))
                .clip(0.0, 1.0)
            )
            .otherwise(None)
            .alias("relative_error"),
        )
        .with_columns(
            pl.when(
                pl.col("reference").is_null() & pl.col("calculated_raw").is_null()
            )
            .then(pl.lit(STATUS_MISSING_BOTH))
            .when(pl.col("reference").is_null())
            .then(pl.lit(STATUS_NO_REFERENCE))
            .when(
                pl.col("calculated_raw").is_null() & (pl.col("indicator") == POWER)
            )
            .then(pl.lit(STATUS_NO_CALCULATED))
            .when(pl.col("denominator") <= 0)
            .then(pl.lit(STATUS_ZERO_DENOMINATOR))
            .when(pl.col("calculated_raw").is_null())
            .then(pl.lit(STATUS_REFERENCE_ONLY))
            .otherwise(pl.lit(STATUS_OK))
            .alias("status")
        )
    )
    return table.select(
        "code",
        "indicator",
        "calculated",
        "reference",
        "difference",
        "denominator",
        "relative_error",
        "status",
    )


def fidelity_summary(error_table: pl.DataFrame) -> pl.DataFrame:
    """Mean capped relative error per country with indicator coverage.

    Only indicators with a usable relative error contribute; the count
    of contributing indicators is reported as ``indicator_coverage``.
    """
    usable = error_table.filter(pl.col("relative_error").is_not_null())
    return usable.group_by("code", maintain_order=True).agg(
        pl.col("relative_error").mean().alias("mean_capped_relative_error"),
        pl.len().cast(int).alias("indicator_coverage"),
    )


def fidelity_label(mean_error: float | None) -> str:
    """Descriptive label from the mean capped relative error.

    Excellent <= 0.40; Good > 0.40 and <= 0.60; Low > 0.60. The
    thresholds were introduced retrospectively during revision.
    """
    if mean_error is None:
        return "N/A"
    if mean_error <= 0.40:
        return "Excellent"
    if mean_error <= 0.60:
        return "Good"
    return "Low"


def fidelity_label_records(
    summary: pl.DataFrame,
    dataset_of_country: dict[str, str],
    snapshot_of_dataset: dict[str, str],
    substitution_notes: dict[str, str] | None = None,
    na_entries: list[dict] | None = None,
) -> list[dict]:
    """Fidelity labels with evidence and provenance.

    Every label carries the mean capped relative error it derives
    from, the number of contributing indicators, and the source
    dataset and snapshot behind the calculated values. N/A entries
    (countries without a calculated analysis) are exported separately
    from computed Low outcomes, each with its explicit reason.
    ``substitution_notes`` marks source substitutions: the Swedish and
    Finnish comparisons are NOBIL-derived, not measurements of their
    separately assessed datasets (se.1, fi.1).
    """
    substitution_notes = substitution_notes or {}
    records = []
    for row in summary.iter_rows(named=True):
        code = row["code"]
        dataset_id = dataset_of_country.get(code)
        records.append(
            {
                "code": code,
                "label": fidelity_label(row["mean_capped_relative_error"]),
                "mean_capped_relative_error": row["mean_capped_relative_error"],
                "indicator_coverage": row["indicator_coverage"],
                "source_dataset_id": dataset_id,
                "source_snapshot_id": snapshot_of_dataset.get(dataset_id),
                "substitution_note": substitution_notes.get(code),
                "na_reason": None,
            }
        )
    for entry in na_entries or []:
        records.append(
            {
                "code": entry["code"],
                "label": "N/A",
                "mean_capped_relative_error": None,
                "indicator_coverage": 0,
                "source_dataset_id": entry.get("source_dataset_id"),
                "source_snapshot_id": entry.get("source_snapshot_id"),
                "substitution_note": None,
                "na_reason": entry["na_reason"],
            }
        )
    return records


def fidelity_labels_for(
    summary: pl.DataFrame,
    config,
    na_reason_overrides: dict[str, str] | None = None,
) -> list[dict]:
    """Fidelity labels for a run, derived from the run configuration.

    ``config`` is a run_config.RunConfig. Countries of the comparison
    get computed labels; countries whose assessed datasets contribute
    no calculated comparison get explicit N/A reasons (separate from
    computed Low outcomes). ``na_reason_overrides`` lets a caller
    record analysis-derived reasons (e.g. a parsed source without
    EVSE records); the fallback reason states that no calculated
    values exist.
    """
    overrides = na_reason_overrides or {}

    # Comparison countries map to the analysis dataset that covers
    # them (SE/FI map to the NOBIL substitution no.1, not to their
    # unacquired datasets); remaining dataset countries map to their
    # own assessed dataset for the N/A entries.
    dataset_of_country: dict[str, str] = {}
    for entry in config.datasets:
        if entry.include_in_analysis:
            for country in entry.country_coverage:
                dataset_of_country[country] = entry.dataset_id
    for entry in config.datasets:
        for country in entry.country_coverage:
            dataset_of_country.setdefault(country, entry.dataset_id)

    snapshot_of_dataset = {
        d.dataset_id: d.snapshot_id for d in config.datasets
    }

    substitution_notes = {
        "SE": (
            "Source substitution: the calculated values derive from the "
            "NOBIL dump (no.1), not from the separately assessed Swedish "
            "dataset se.1, which could not be acquired."
        ),
        "FI": (
            "Source substitution: the calculated values derive from the "
            "NOBIL dump (no.1), not from the separately assessed Finnish "
            "dataset fi.1, which could not be acquired."
        ),
        "DK": (
            "No separately assessed Danish dataset; the calculated "
            "values derive from the NOBIL dump (no.1)."
        ),
        "IS": (
            "No separately assessed Icelandic dataset; the calculated "
            "values derive from the NOBIL dump (no.1)."
        ),
    }

    compared = set(summary["code"].to_list())
    na_entries = []
    for country, dataset_id in dataset_of_country.items():
        if country in compared:
            continue
        entry = config.entry(dataset_id)
        reason = overrides.get(country) or entry.exclusion_reason or (
            "Dataset included in the graph analysis but no calculated "
            "values were produced for this country."
        )
        na_entries.append(
            {
                "code": country,
                "source_dataset_id": dataset_id,
                "source_snapshot_id": entry.snapshot_id,
                "na_reason": reason,
            }
        )

    return fidelity_label_records(
        summary,
        dataset_of_country,
        snapshot_of_dataset,
        substitution_notes,
        na_entries,
    )


def heatmap_category_expr(col: str) -> pl.Expr:
    """Widget colour category for a relative-error column.

    Reproduces the notebook's seven-level scale: 0 = no fidelity
    (error >= 1), 6 = (unreachable for absolute errors) below 0.
    """
    return (
        pl.col(col)
        .cut(
            breaks=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
            left_closed=True,
            labels=["6", "5", "4", "3", "2", "1", "0"],
        )
        .alias("cat")
    )


def heatmap_frame(
    error_table: pl.DataFrame, summary: pl.DataFrame
) -> pl.DataFrame:
    """Long frame consumed by HeatMapWidget: code, range, error, cat.

    Row order matches the published figure: countries sorted by code,
    indicators in INDICATORS order followed by the overall fidelity.
    """
    wide = error_table.pivot(index="code", on="indicator", values="relative_error")
    wide = (
        wide.join(
            summary.select("code", pl.col("mean_capped_relative_error").alias(OVERALL)),
            on="code",
            how="inner",
        )
        .sort("code")
    )
    return wide.unpivot(
        index="code", variable_name="range", value_name="error"
    ).with_columns(heatmap_category_expr("error"))
