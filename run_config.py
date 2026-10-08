"""Loader and validation for the run configuration manifest.

``run_config.yaml`` is the checked-in manifest that makes input and
source selection reproducible: it records, per dataset, the stable
dataset ID, the snapshot date and its meaning, the input path, a
checksum, whether the dataset is part of the analysis, the country
coverage, and the reason for any exclusion.

The notebook (main.py) and the extractor (extract_data.py) select
sources through this module instead of hard-coded filenames or
notebook checkbox state.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "run_config.yaml"


@dataclass(frozen=True)
class InputFile:
    path: Path
    checksum: str | None = None

    def verify(self) -> bool:
        """True if the file exists and matches its sha256 checksum."""
        if not self.path.exists():
            return False
        if self.checksum is None:
            return True
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        return f"sha256:{digest}" == self.checksum


@dataclass(frozen=True)
class DatasetEntry:
    dataset_id: str
    format: str
    snapshot_id: str
    snapshot_date: date | None
    snapshot_meaning: str
    input_file: InputFile | None
    parsed_dir: str | None
    include_in_analysis: bool
    country_coverage: list[str]
    # Rows outside these countries are dropped during graph expansion.
    # Empty/None keeps the historical unfiltered expansion (national
    # publications whose coverage is the country itself).
    expansion_country_filter: list[str] = field(default_factory=list)
    exclusion_reason: str | None = None

    @property
    def country(self) -> str:
        """The dataset's home country (prefix of the dataset ID)."""
        return self.dataset_id.split(".")[0].upper()


@dataclass(frozen=True)
class EafoReference:
    snapshot_id: str
    snapshot_date: date
    meaning: str
    inputs: list[InputFile] = field(default_factory=list)


@dataclass(frozen=True)
class RunConfig:
    analysis_name: str
    eafo_reference: EafoReference
    datasets: list[DatasetEntry]

    def entry(self, dataset_id: str) -> DatasetEntry:
        for entry in self.datasets:
            if entry.dataset_id == dataset_id:
                return entry
        raise KeyError(f"dataset {dataset_id!r} not in run_config.yaml")

    def entry_by_parsed_dir(self, parsed_dir: str) -> DatasetEntry:
        for entry in self.datasets:
            if entry.parsed_dir == parsed_dir:
                return entry
        raise KeyError(f"parsed dir {parsed_dir!r} not in run_config.yaml")

    def analysis_datasets(self) -> list[DatasetEntry]:
        """Datasets included in the graph analysis, in manifest order."""
        return [d for d in self.datasets if d.include_in_analysis]

    def excluded_datasets(self) -> list[DatasetEntry]:
        return [d for d in self.datasets if not d.include_in_analysis]

    def coverage_of(self, dataset_id: str) -> list[str]:
        return list(self.entry(dataset_id).country_coverage)


def _parse_date(value) -> date | None:
    if value in (None, ""):
        return None
    return date.fromisoformat(str(value))


def _input_file(raw: dict | None, root: Path) -> InputFile | None:
    if not raw or not raw.get("path"):
        return None
    path = Path(raw["path"])
    if not path.is_absolute():
        path = root / path
    return InputFile(path=path, checksum=raw.get("checksum"))


def _dataset_input_file(d: dict, root: Path) -> InputFile | None:
    if not d.get("input_path"):
        return None
    path = Path(d["input_path"])
    if not path.is_absolute():
        path = root / path
    return InputFile(path=path, checksum=d.get("checksum"))


def load(path: Path = CONFIG_PATH) -> RunConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    root = path.resolve().parent
    analysis = raw["analysis"]
    eafo = analysis["eafo_reference"]

    datasets: list[DatasetEntry] = []
    seen: set[str] = set()
    for d in raw["datasets"]:
        dataset_id = d["dataset_id"]
        if dataset_id in seen:
            raise ValueError(f"duplicate dataset_id in run config: {dataset_id}")
        seen.add(dataset_id)
        datasets.append(
            DatasetEntry(
                dataset_id=dataset_id,
                format=d["format"],
                snapshot_id=d["snapshot_id"],
                snapshot_date=_parse_date(d.get("snapshot_date")),
                snapshot_meaning=d.get("snapshot_meaning", ""),
                input_file=_dataset_input_file(d, root),
                parsed_dir=d.get("parsed_dir"),
                include_in_analysis=bool(d.get("include_in_analysis", False)),
                country_coverage=list(d.get("country_coverage", [])),
                expansion_country_filter=list(
                    d.get("expansion_country_filter") or []
                ),
                exclusion_reason=d.get("exclusion_reason"),
            )
        )

    config = RunConfig(
        analysis_name=analysis["name"],
        eafo_reference=EafoReference(
            snapshot_id=eafo["snapshot_id"],
            snapshot_date=_parse_date(eafo["snapshot_date"]),
            meaning=eafo.get("meaning", ""),
            inputs=[
                _input_file(i, root) for i in eafo.get("inputs", [])
            ],
        ),
        datasets=datasets,
    )
    _validate(config)
    return config


def _validate(config: RunConfig) -> None:
    problems: list[str] = []

    included = config.analysis_datasets()
    if not included:
        problems.append("no dataset is included in the analysis")

    for entry in config.datasets:
        if entry.include_in_analysis:
            if entry.input_file is None:
                problems.append(
                    f"{entry.dataset_id}: included in the analysis but no input_path"
                )
            if not entry.country_coverage:
                problems.append(
                    f"{entry.dataset_id}: included in the analysis but no country_coverage"
                )
        elif not entry.exclusion_reason:
            problems.append(
                f"{entry.dataset_id}: excluded without an exclusion_reason"
            )

    # Source overlap must not duplicate national counts: a country may
    # be covered by more than one included dataset only if the datasets
    # agree on it (currently the Nordic countries come from NOBIL
    # alone; se.1/fi.1 are not acquired).
    coverage: dict[str, list[str]] = {}
    for entry in included:
        for country in entry.country_coverage:
            coverage.setdefault(country, []).append(entry.dataset_id)
    for country, dataset_ids in coverage.items():
        if len(dataset_ids) > 1:
            problems.append(
                f"country {country} covered by multiple included datasets "
                f"({', '.join(dataset_ids)}); national counts would be duplicated"
            )

    if problems:
        raise ValueError("invalid run configuration:\n  " + "\n  ".join(problems))


def verify_checksums(config: RunConfig) -> list[str]:
    """Verify all recorded checksums; return a list of problems."""
    problems: list[str] = []

    def check(file: InputFile | None, label: str) -> None:
        if file is None:
            return
        if not file.path.exists():
            problems.append(f"{label}: missing input {file.path}")
        elif not file.verify():
            problems.append(f"{label}: checksum mismatch for {file.path}")

    for entry in config.datasets:
        check(entry.input_file, entry.dataset_id)
    for file in config.eafo_reference.inputs:
        check(file, f"eafo_reference/{file.path.name}")
    return problems
