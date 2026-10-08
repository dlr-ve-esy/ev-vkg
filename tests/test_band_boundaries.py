"""Exact boundary values of the calculated power-band binning.

Audit item: the calculated and EAFO reference bands differ at 7.4, 50
and 150 kW; the query boundaries must be explicit and tested. The
mirror of queries/total_evses_per_power.sparql is
error_metrics.band_of_power: inclusive upper bounds except the
150-350 kW bin (< 350 kW), so a connector rated exactly 350 kW lands
in "350+ kW".
"""

import pytest

import error_metrics as em


@pytest.mark.parametrize(
    "watts,expected",
    [
        (0, "0-7,4 kW"),
        (7400, "0-7,4 kW"),  # inclusive upper bound
        (7401, "7,4-22 kW"),
        (22000, "7,4-22 kW"),  # inclusive
        (22001, "22-50 kW"),
        (50000, "22-50 kW"),  # inclusive
        (50001, "50-150 kW"),
        (150000, "50-150 kW"),  # inclusive
        (150001, "150-350 kW"),
        (349999, "150-350 kW"),
        (350000, "350+ kW"),  # 150-350 is half-open: exactly 350 kW is 350+
        (350001, "350+ kW"),
        (1000000, "350+ kW"),
    ],
)
def test_band_boundary(watts, expected):
    assert em.band_of_power(watts) == expected


def test_bands_are_the_six_published_bands():
    assert em.BANDS == [
        "0-7,4 kW",
        "7,4-22 kW",
        "22-50 kW",
        "50-150 kW",
        "150-350 kW",
        "350+ kW",
    ]


def test_band_sum_is_labelled_as_band_sum():
    """The sum of per-band counts is not a deduplicated EVSE total."""
    assert em.BAND_SUM == "EVSE band sum"
    assert em.BAND_SUM in em.INDICATORS
