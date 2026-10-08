# Public EV charging infrastructure virtual knowledge graph

This repository is the code supporting the publication "Are European electric vehicle charging infrastructure data machine-actionable? A FAIR assessment through virtual knowledge graphs".

## Usage

To work with this repository you need to acquire the data from
 [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17422740.svg)](https://doi.org/10.5281/zenodo.17422740). The script `get_data.py` can be used to download it automatically and saved in the right folder.

The archived version of the analysis code is available at [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17435147.svg)](https://doi.org/10.5281/zenodo.17435147).

This repository depends on work from other contexts, the external repository can be imported by using the terminal to go to this folder after cloning and using git.

```bash
git submodule update --init --recursive
```

Once the data is in the main folder you need to install the dependencies. I recommend using [uv](https://github.com/astral-sh/uv) which will manage these for you. But any python package management should work. Otherwise using your favorite python environment management tool you can activate your env and install:

```bash
pip install -e .
```
To get the archived version of the data you can run the `get_data.py` script.

```bash
python get_data.py
```
Or with uv:

```bash
uv run get_data.py
```

The knowledge graph can be built and explored using the marimo notebook `main.py`, calling:

```bash
uv run marimo edit main.py
```

Or using the pip installation of marimo, calling:

```bash
marimo edit main.py
```

## Execution model

The mappings materialise the RDF graph eagerly in memory within the Python process: maplib (0.15.33) expands the OTTR mappings into an in-memory Rust/Oxigraph store. There is no persistent triple store and no external database; the graph exists only for the duration of the notebook session. The charging ontology (CHIO 0.2.0) is fetched at runtime from the charging-ontology static site if it is not already present locally.

## Provenance notes

- The NOBIL source (Norway) also covers DK/FI/IS/SE and is expanded unfiltered; the published Nordic values were produced this way.
- The power indicator ("Total Power MW") is the sum over EVSEs of the minimum connector power, i.e. a lower bound on the installed power.
- The German values published in the paper come from the May 2025 BNetZA snapshot (Stand 07.05.2025). The archive file named `bnetza_charging_stations_raw_08_2025.xlsx` actually contains the July 2025 snapshot (Stand 18.07.2025); the snapshot to parse is configured through `BNETZA_SNAPSHOT` in `extract_data.py`.
- The DATEX II profile generator and code generation tool versions used for the profile-driven parsing of the archived run were not recorded and cannot be recovered retroactively; record them in `datex2/TOOL_VERSIONS.md` for future runs.
