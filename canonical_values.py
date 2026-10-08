"""Canonical published values for the figure pipeline.

Every figure input in ``viz_data/`` must reproduce the published
manuscript tables (author decision Q2: the published values are
canonical). This module holds those values in one place so that

1. ``write_canonical_query_results.py`` can regenerate the committed
   ``viz_data/query_results/*.json`` files from the published state, and
2. ``export_widget_pngs.py`` can assert, before rendering anything, that
   the figure inputs still reproduce the tables (guard M-3 of the figure
   export changes).

Sources:
- Table 6 (tab:quantities): EVSE counts and power, calculated vs EAFO
  reference vs AFIR target, twelve countries including IS and NO.
- Table 7 (tab:capacities): charger counts by power rating, calculated
  vs EAFO reference, six bands, twelve countries.
- Table 8 (tab:holistic-assessment): FAIR totals per dataset (23
  datasets). The per-dimension split below was derived by applying the
  notebook's scoring rules (main.py, FAIR scoring cell) to the final
  ``sources/metadata.csv``; every total reproduces Table 8 exactly.
"""

# ---------------------------------------------------------------------------
# Table 8: FAIR scores per dataset (23 datasets, two German ones)
# ---------------------------------------------------------------------------

# code -> (country, provider, F, A, I, R)
FAIR_DATASET_SCORES = {
    "de.1": ("DE", "Eco-Movement", 3, 3, 3, 3),
    "ch.1": ("CH", "Bundesamt für Energie", 2, 3, 3, 3),
    "fr.1": ("FR", "data.gouv.fr", 3, 3, 1, 3),
    "no.1": ("NO", "NOBIL", 3, 3, 1, 3),
    "at.1": ("AT", "ladestellen.at", 3, 3, 3, 1),
    "cy.1": ("CY", "Fix Cyprus", 3, 1, 2, 3),
    "lv.1": ("LV", "Latvian State Roads", 3, 1, 3, 2),
    "es.1": ("ES", "General Traffic Directorate", 2, 1, 3, 2),
    "pt.1": ("PT", "MOBI.E", 3, 1, 3, 0),
    "de.2": ("DE", "German Network Agency", 2, 1, 1, 3),
    "be.1": ("BE", "Eco-Movement", 3, 0, 3, 0),
    "se.1": ("SE", "Eco-Movement", 3, 0, 3, 0),
    "si.1": ("SI", "NAP Slovenia", 2, 1, 3, 0),
    "hu.1": ("HU", "Magyar Közút", 2, 1, 2, 0),
    "lu.1": ("LU", "Chargy", 3, 1, 0, 1),
    "uk.1": ("UK", "Zapmap", 1, 0, 3, 0),
    "it.1": ("IT", "Unique National Platform", 0, 0, 3, 0),
    "fi.1": ("FI", "latauskartta.fi", 2, 0, 0, 0),
    "nl.1": ("NL", "Eco-Movement", 2, 0, 0, 0),
    "lt.1": ("LT", "Lithuanian register", 0, 1, 0, 0),
    "el.1": ("EL", "Fortisis", 0, 0, 0, 0),
    "mt.1": ("MT", "Charge my Ride", 0, 0, 0, 0),
    "pl.1": ("PL", "Greenway", 0, 0, 0, 0),
}

# Country-level totals the country figure input must reproduce
# (the German country score is de.2, the dataset used in the
# quantitative comparison).
FAIR_COUNTRY_TOTALS = {
    "AT": 10, "BE": 6, "CH": 11, "CY": 9, "DE": 7, "EL": 0, "ES": 8,
    "FI": 2, "FR": 10, "HU": 5, "IT": 3, "LT": 1, "LU": 5, "LV": 9,
    "MT": 0, "NL": 2, "NO": 10, "PL": 0, "PT": 7, "SE": 6, "SI": 6,
    "UK": 4,
}

# ---------------------------------------------------------------------------
# Table 6 (tab:quantities): power indicator, MW
# ---------------------------------------------------------------------------

# code -> (category, calculated MW, EAFO reference MW, AFIR target MW)
PUBLISHED_QUANTITIES = {
    "AT": ("Austria", 1196, 1182, 360),
    "DE": ("Germany", 9159, 7907, 3139),
    "DK": ("Denmark", 629, 1660, 625),
    "ES": ("Spain", 630, 1448, 508),
    "FI": ("Finland", 295, 830, 302),
    "FR": ("France", 6846, 5640, 2431),
    "IS": ("Iceland", 31, None, None),
    "LV": ("Latvia", 66, 72, 10),
    "NO": ("Norway", 2634, None, None),
    "PT": ("Portugal", 567, 471, 358),
    "SE": ("Sweden", 2105, 2465, 752),
    "SI": ("Slovenia", 46, 90, 25),
}

# ---------------------------------------------------------------------------
# Table 7 (tab:capacities): charger counts by power rating
# ---------------------------------------------------------------------------

BANDS = [
    "0-7,4 kW",
    "7,4-22 kW",
    "22-50 kW",
    "50-150 kW",
    "150-350 kW",
    "350+ kW",
]

# code -> [six calculated band counts] (None where the table is blank)
PUBLISHED_CAPACITIES_CALC = {
    "AT": [1199, 19618, 1802, 2609, 1399, 284],
    "DE": [3335, 122812, 8042, 11528, 14649, 2385],
    "DK": [13, 8766, 292, 421, 873, 358],
    "ES": [3025, 7550, 4171, 1638, 233, 204],
    "FI": [108, 3862, 123, 86, 342, 286],
    "FR": [29936, 58778, 16329, 10804, 11329, 1902],
    "IS": [4, 778, 32, 52, 24, None],
    "LV": [6, 155, 206, 51, 52, 2],
    "NO": [7712, 10672, 2728, 4307, 4863, 1560],
    "PT": [3201, 7664, 2537, 1988, 364, 50],
    "SE": [9281, 27611, 1227, 2102, 2576, 1627],
    "SI": [405, 1278, 258, 34, 44, None],
}

# code -> [six EAFO reference band counts]
PUBLISHED_CAPACITIES_REF = {
    "AT": [647, 24974, 703, 2361, 3797, 651],
    "DE": [1922, 129452, 2954, 7848, 19644, 9759],
    "DK": [65, 33920, 2042, 1659, 4120, 762],
    "ES": [2194, 28531, 2592, 6362, 2659, 526],
    "FI": [105, 12523, 39, 1198, 2463, 888],
    "FR": [54189, 80080, 5817, 10974, 9292, 8959],
    "IS": [10, 2100, 17, 116, 347, 124],
    "LV": [2, 581, 199, 232, 306, 8],
    "NO": [4252, 15285, 101, 1644, 7310, 1399],
    "PT": [872, 8106, 720, 2732, 733, 84],
    "SE": [9074, 41304, 575, 1263, 5999, 1629],
    "SI": [18, 1874, 126, 212, 99, 64],
}


def dataset_scores_records() -> list:
    """FAIR dataset scores as a list of records, sorted by total (desc)."""
    records = []
    for code, (country, provider, f, a, i, r) in FAIR_DATASET_SCORES.items():
        records.append(
            {
                "code": code,
                "country": country,
                "provider": provider,
                "F": f,
                "A": a,
                "I": i,
                "R": r,
                "TOTAL": f + a + i + r,
            }
        )
    records.sort(key=lambda r: (-r["TOTAL"], r["code"]))
    return records


def results_records() -> list:
    """The published results frame as query_results/results.json rows."""
    rows = []
    for code, (category, calc, ref, target) in PUBLISHED_QUANTITIES.items():
        rows.append(
            {
                "Category": category,
                "Code": code,
                "Target kW": None if target is None else target * 1000,
                "Total power (kW) output": None if ref is None else ref * 1000,
                "target_mw": target,
                "total_mw": ref,
                "total_accounted_power": calc,
            }
        )
    return rows


def band_records(published: dict) -> list:
    """Band-count frames as chart_input / chart_input_2 rows."""
    rows = []
    for code, counts in published.items():
        row = {"code": code}
        for band, count in zip(BANDS, counts):
            row[band] = count
        rows.append(row)
    return rows


def filtered_markers() -> dict:
    """AFIR targets for the countries that report to the EAFO."""
    return {
        code: target
        for code, (_, _, _, target) in PUBLISHED_QUANTITIES.items()
        if target is not None
    }


def assert_fair_country_scores(fair_scores: dict) -> None:
    """D-1 regression check: country totals must reproduce Table 8."""
    problems = []
    for country, expected in FAIR_COUNTRY_TOTALS.items():
        got = fair_scores.get(country, {}).get("TOTAL")
        if got != expected:
            problems.append(
                f"{country}: expected TOTAL {expected}, got {got}"
            )
    if problems:
        raise AssertionError(
            "viz_data/fair_scores.json deviates from canonical Table 8: "
            + "; ".join(problems)
        )


def assert_dataset_scores(records: list) -> None:
    """The dataset-level scores file must reproduce Table 8 totals."""
    by_code = {r["code"]: r for r in records}
    if len(by_code) != len(FAIR_DATASET_SCORES):
        raise AssertionError(
            f"expected {len(FAIR_DATASET_SCORES)} datasets, "
            f"got {len(by_code)}"
        )
    problems = []
    for code, (country, _, f, a, i, r) in FAIR_DATASET_SCORES.items():
        rec = by_code.get(code)
        if rec is None:
            problems.append(f"{code}: missing")
            continue
        expected = {"F": f, "A": a, "I": i, "R": r, "TOTAL": f + a + i + r}
        for key, value in expected.items():
            if rec.get(key) != value:
                problems.append(
                    f"{code}.{key}: expected {value}, got {rec.get(key)}"
                )
    if problems:
        raise AssertionError(
            "fair_scores_datasets.json deviates from canonical Table 8: "
            + "; ".join(problems)
        )


def assert_results(rows: list) -> None:
    """results.json must reproduce the published Table 6 power values."""
    by_code = {r["Code"]: r for r in rows}
    problems = []
    for code, (_, calc, ref, target) in PUBLISHED_QUANTITIES.items():
        row = by_code.get(code)
        if row is None:
            problems.append(f"{code}: missing")
            continue
        if row.get("total_accounted_power") != calc:
            problems.append(
                f"{code} calculated: expected {calc}, "
                f"got {row.get('total_accounted_power')}"
            )
        if row.get("total_mw") != ref:
            problems.append(
                f"{code} EAFO reference: expected {ref}, "
                f"got {row.get('total_mw')}"
            )
        if row.get("target_mw") != target:
            problems.append(
                f"{code} AFIR target: expected {target}, "
                f"got {row.get('target_mw')}"
            )
    if problems:
        raise AssertionError(
            "query_results/results.json deviates from canonical Table 6: "
            + "; ".join(problems)
        )


def assert_band_counts(rows: list, published: dict, label: str) -> None:
    """Band-count frames must reproduce the published Table 7 columns."""
    by_code = {r["code"]: r for r in rows}
    problems = []
    for code, counts in published.items():
        row = by_code.get(code)
        if row is None:
            problems.append(f"{code}: missing")
            continue
        for band, expected in zip(BANDS, counts):
            if row.get(band) != expected:
                problems.append(
                    f"{code} {band}: expected {expected}, got {row.get(band)}"
                )
    if problems:
        raise AssertionError(
            f"{label} deviates from canonical Table 7: " + "; ".join(problems)
        )


def assert_filtered_markers(markers: dict) -> None:
    """AFIR target markers must reproduce the published target column."""
    expected = filtered_markers()
    if markers != expected:
        raise AssertionError(
            f"query_results/filtered_markers.json deviates from the "
            f"published AFIR targets: expected {expected}, got {markers}"
        )
