"""Regression checks for the run configuration manifest (audit item 6).

The manifest is the single source of truth for input and source
selection: the notebook and the extractor must be able to run from it
without manual checkbox choices, and every output must identify its
actual input versions.
"""

from datetime import date

import run_config as rc


def test_manifest_has_23_datasets():
    config = rc.load()
    assert len(config.datasets) == 23
    ids = [d.dataset_id for d in config.datasets]
    assert len(set(ids)) == 23  # stable dataset IDs are unique


def test_analysis_dataset_selection():
    config = rc.load()
    included = {d.dataset_id for d in config.analysis_datasets()}
    assert included == {
        "at.1",
        "cy.1",
        "de.2",
        "es.1",
        "fr.1",
        "lv.1",
        "no.1",
        "pt.1",
        "si.1",
    }


def test_de1_excluded_with_reason_de2_included():
    config = rc.load()
    de1 = config.entry("de.1")
    assert not de1.include_in_analysis
    assert de1.exclusion_reason  # explicit, not silently dropped
    de2 = config.entry("de.2")
    assert de2.include_in_analysis
    assert de2.snapshot_date == date(2025, 5, 7)  # May workbook, not July


def test_nobil_covers_five_nordic_countries():
    config = rc.load()
    no1 = config.entry("no.1")
    assert no1.country_coverage == ["NO", "DK", "FI", "IS", "SE"]
    assert no1.expansion_country_filter == ["NO", "DK", "FI", "IS", "SE"]


def test_dates_parsed_as_dates():
    config = rc.load()
    for entry in config.datasets:
        if entry.input_file is not None:
            assert entry.snapshot_date is not None
            assert isinstance(entry.snapshot_date, date)
    assert config.entry("fr.1").snapshot_date == date(2025, 6, 10)
    assert config.entry("no.1").snapshot_date == date(2025, 1, 20)


def test_eafo_reference_snapshot():
    config = rc.load()
    assert config.eafo_reference.snapshot_id == "eafo-20250617"
    assert config.eafo_reference.snapshot_date == date(2025, 6, 17)
    assert len(config.eafo_reference.inputs) == 2


def test_checksums_verify():
    config = rc.load()
    problems = rc.verify_checksums(config)
    assert problems == []


def test_snapshot_ids_do_not_encode_dataset_identity():
    """Dataset identity is the stable dataset_id; snapshot IDs may
    contain dates but must not be used to select records by substring."""
    config = rc.load()
    for entry in config.datasets:
        assert entry.dataset_id.count(".") == 1
        assert entry.dataset_id.split(".")[0].upper() == entry.country


def test_excluded_datasets_all_have_reasons():
    config = rc.load()
    for entry in config.excluded_datasets():
        assert entry.exclusion_reason, f"{entry.dataset_id} excluded without reason"


def test_switzerland_exclusion_is_explicit():
    config = rc.load()
    ch = config.entry("ch.1")
    assert not ch.include_in_analysis
    # EAFO count and power references exist for Switzerland; the reason
    # must record the missing analysis, not claim missing reference data.
    assert "do exist" in ch.exclusion_reason
